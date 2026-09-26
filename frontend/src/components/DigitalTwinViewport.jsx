import React, { useEffect, useRef, useState, useCallback } from 'react';
import { cadApi } from '../api/cad';
import { MorphingInfinity } from './loading-ui/morphing-infinity';
import { TextShimmer } from './loading-ui/text-shimmer';

let babylonLoadPromise = null;
function ensureBabylon() {
  if (typeof window !== 'undefined' && window.BABYLON) {
    return Promise.resolve(window.BABYLON);
  }
  if (!babylonLoadPromise) {
    babylonLoadPromise = new Promise((resolve, reject) => {
      const existing = document.querySelector('script[data-babylon]');
      if (existing) {
        if (window.BABYLON) return resolve(window.BABYLON);
        existing.addEventListener('load', () => resolve(window.BABYLON));
        existing.addEventListener('error', reject);
        return;
      }
      const script = document.createElement('script');
      script.src = '/babylon.js';
      script.async = true;
      script.setAttribute('data-babylon', 'true');
      script.onload = () => resolve(window.BABYLON);
      script.onerror = (err) => reject(err);
      document.head.appendChild(script);
    });
  }
  return babylonLoadPromise;
}

/**
 * Babylon.js 3D CAD Digital Twin Viewport.
 * Connects directly to authoritative backend CAD pipeline.
 * Renders bounding envelopes, component hierarchy, spatial telemetry,
 * and authoritative geometry traces.
 */
export function DigitalTwinViewport({
  jobId,
  onUploadClick,
  onMeasurementsLoaded,
  onMapToDNASuccess,
}) {
  const canvasRef = useRef(null);
  const engineRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const meshObjectsRef = useRef([]);

  const [activePreset, setActivePreset] = useState('iso');
  const [cadModel, setCadModel] = useState(null);
  const [cadModels, setCadModels] = useState([]);
  const [meshData, setMeshData] = useState(null);
  const [measurements, setMeasurements] = useState([]);
  const [components, setComponents] = useState([]);
  const [selectedMeasurement, setSelectedMeasurement] = useState(null);
  const [traceData, setTraceData] = useState(null);
  const [traceLoading, setTraceLoading] = useState(false);
  const [mappingLoading, setMappingLoading] = useState(false);
  const [mappingMessage, setMappingMessage] = useState(null);
  const [viewerState, setViewerState] = useState('NO_CAD'); // NO_CAD, CAD_UPLOADED, CAD_PROCESSING, CAD_READY, CAD_REQUIRES_REVIEW, CAD_FAILED

  // Load CAD Models for the job
  const loadJobCAD = useCallback(async () => {
    if (!jobId) {
      setViewerState('NO_CAD');
      return;
    }
    try {
      const models = await cadApi.getCADModels(jobId);
      setCadModels(models);
      if (models && models.length > 0) {
        const active = models[0];
        setCadModel(active);

        // Map status to viewer state
        const status = active.processing_status;
        if (status === 'MEASUREMENTS_AVAILABLE' || status === 'GEOMETRY_EXTRACTED' || status === 'PARSED') {
          setViewerState('CAD_READY');
          // Load mesh, measurements, components
          const [meshRes, measRes, compRes] = await Promise.all([
            cadApi.getCADMesh(jobId, active.id).catch(() => null),
            cadApi.getCADMeasurements(jobId, active.id).catch(() => []),
            cadApi.getCADComponents(jobId, active.id).catch(() => []),
          ]);

          if (meshRes && meshRes.mesh) setMeshData(meshRes.mesh);
          if (measRes) {
            setMeasurements(measRes);
            if (onMeasurementsLoaded) onMeasurementsLoaded(measRes);
          }
          if (compRes) setComponents(compRes);
        } else if (status === 'UPLOADED' || status === 'QUEUED' || status === 'PROCESSING') {
          setViewerState('CAD_PROCESSING');
        } else if (status === 'REQUIRES_REVIEW') {
          setViewerState('CAD_REQUIRES_REVIEW');
        } else if (status === 'FAILED') {
          setViewerState('CAD_FAILED');
        }
      } else {
        setViewerState('NO_CAD');
        setCadModel(null);
        setMeshData(null);
        setMeasurements([]);
        setComponents([]);
      }
    } catch (err) {
      console.warn('Failed to load job CAD data:', err);
      setViewerState('NO_CAD');
    }
  }, [jobId, onMeasurementsLoaded]);

  useEffect(() => {
    loadJobCAD();
  }, [loadJobCAD]);

  // Initialize Babylon.js Scene
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let active = true;

    ensureBabylon().then((BABYLON) => {
      if (!active || !canvasRef.current || !BABYLON) return;

      try {
        const engine = new BABYLON.Engine(canvas, true, { preserveDrawingBuffer: true, stencil: true });
        engineRef.current = engine;

        const scene = new BABYLON.Scene(engine);
        sceneRef.current = scene;
        scene.clearColor = new BABYLON.Color4(0.027, 0.039, 0.071, 1.0); // #070A12

      // Camera: ArcRotateCamera
      const camera = new BABYLON.ArcRotateCamera(
        'cadCam',
        -Math.PI / 3,
        Math.PI / 3.2,
        30,
        new BABYLON.Vector3(0, 0, 0),
        scene
      );
      camera.attachControl(canvas, true);
      camera.lowerRadiusLimit = 5;
      camera.upperRadiusLimit = 150;
      camera.wheelPrecision = 30;
      cameraRef.current = camera;

      // Lights
      const hemiLight = new BABYLON.HemisphericLight('hemiLight', new BABYLON.Vector3(0, 1, 0), scene);
      hemiLight.intensity = 0.85;
      hemiLight.diffuse = new BABYLON.Color3(0.9, 0.95, 1.0);

      const dirLight = new BABYLON.DirectionalLight('dirLight', new BABYLON.Vector3(-1, -2, -1), scene);
      dirLight.position = new BABYLON.Vector3(20, 40, 20);
      dirLight.intensity = 0.6;

      // Ground Datum Grid
      const gridGround = BABYLON.MeshBuilder.CreateGround('grid', { width: 40, height: 30 }, scene);
      gridGround.position.y = -0.05;
      const groundMat = new BABYLON.StandardMaterial('groundMat', scene);
      groundMat.diffuseColor = new BABYLON.Color3(0.04, 0.07, 0.12);
      groundMat.specularColor = new BABYLON.Color3(0.02, 0.04, 0.08);
      gridGround.material = groundMat;

      // Coordinate axes
      const axisX = BABYLON.MeshBuilder.CreateLines(
        'axisX',
        { points: [new BABYLON.Vector3(-20, 0, 0), new BABYLON.Vector3(20, 0, 0)] },
        scene
      );
      axisX.color = new BABYLON.Color3(0.18, 0.35, 0.6);

      const axisZ = BABYLON.MeshBuilder.CreateLines(
        'axisZ',
        { points: [new BABYLON.Vector3(0, 0, -15), new BABYLON.Vector3(0, 0, 15)] },
        scene
      );
      axisZ.color = new BABYLON.Color3(0.18, 0.35, 0.6);

      engine.runRenderLoop(() => {
        if (scene) scene.render();
      });

      const handleResize = () => {
        if (engine) engine.resize();
      };
        window.addEventListener('resize', handleResize);
      } catch (err) {
        console.warn('Babylon.js initialization error:', err);
      }
    });

    return () => {
      active = false;
      if (sceneRef.current) sceneRef.current.dispose();
      if (engineRef.current) engineRef.current.dispose();
    };
  }, []);

  // Update 3D Geometry in Babylon.js when meshData changes
  useEffect(() => {
    const scene = sceneRef.current;
    const BABYLON = window.BABYLON;
    if (!scene || !BABYLON) return;

    // Clean up previous dynamic meshes
    meshObjectsRef.current.forEach((m) => {
      try {
        m.dispose();
      } catch (e) {}
    });
    meshObjectsRef.current = [];

    if (!meshData || viewerState !== 'CAD_READY') return;

    try {
      const dims = meshData.dimensions || [10, 10, 10];
      // Normalize visualization scale so large models fit nicely
      const maxDim = Math.max(dims[0], dims[1], dims[2]) || 1.0;
      const scaleFactor = maxDim > 25 ? 25.0 / maxDim : 1.0;

      const sx = Math.max(dims[0] * scaleFactor, 0.5);
      const sy = Math.max(dims[1] * scaleFactor, 0.5);
      const sz = Math.max(dims[2] * scaleFactor, 0.5);

      // Create Enclosure Bounding Box
      const box = BABYLON.MeshBuilder.CreateBox(
        'cadEnclosureBox',
        { width: sx, height: sy, depth: sz },
        scene
      );
      box.position = new BABYLON.Vector3(0, sy / 2.0, 0);

      const boxMat = new BABYLON.StandardMaterial('boxMat', scene);
      boxMat.diffuseColor = new BABYLON.Color3(0.11, 0.53, 0.89); // Tech cyan-blue
      boxMat.specularColor = new BABYLON.Color3(0.2, 0.7, 1.0);
      boxMat.alpha = 0.35;
      boxMat.wireframe = false;
      box.material = boxMat;
      meshObjectsRef.current.push(box);

      // Add wireframe edge lines for CAD blueprint appearance
      const wireBox = BABYLON.MeshBuilder.CreateBox(
        'wireBox',
        { width: sx * 1.001, height: sy * 1.001, depth: sz * 1.001 },
        scene
      );
      wireBox.position = new BABYLON.Vector3(0, sy / 2.0, 0);
      const wireMat = new BABYLON.StandardMaterial('wireMat', scene);
      wireMat.wireframe = true;
      wireMat.emissiveColor = new BABYLON.Color3(0.2, 0.8, 1.0);
      wireBox.material = wireMat;
      meshObjectsRef.current.push(wireBox);

      // Render Cylindrical Holes/Features if present
      if (meshData.cylinders && meshData.cylinders.length > 0) {
        meshData.cylinders.forEach((cyl, idx) => {
          const r = Math.max((cyl.radius || 2) * scaleFactor, 0.3);
          const cylMesh = BABYLON.MeshBuilder.CreateCylinder(
            `hole_${idx}`,
            { height: sy * 1.02, diameter: r * 2.0 },
            scene
          );
          cylMesh.position = new BABYLON.Vector3(0, sy / 2.0, 0);
          const cylMat = new BABYLON.StandardMaterial(`cylMat_${idx}`, scene);
          cylMat.diffuseColor = new BABYLON.Color3(0.95, 0.4, 0.1);
          cylMat.emissiveColor = new BABYLON.Color3(0.5, 0.15, 0.05);
          cylMesh.material = cylMat;
          meshObjectsRef.current.push(cylMesh);
        });
      }

      // Adjust camera focus
      if (cameraRef.current) {
        cameraRef.current.target = new BABYLON.Vector3(0, sy / 2.0, 0);
        cameraRef.current.radius = Math.max(sx, sy, sz) * 2.5;
      }
    } catch (err) {
      console.warn('Error rendering CAD geometry in Babylon.js:', err);
    }
  }, [meshData, viewerState]);

  const setCameraPreset = (preset) => {
    setActivePreset(preset);
    const camera = cameraRef.current;
    if (!camera) return;

    if (preset === 'ortho') {
      camera.alpha = -Math.PI / 2;
      camera.beta = Math.PI / 2;
    } else if (preset === 'iso') {
      camera.alpha = -Math.PI / 3;
      camera.beta = Math.PI / 3.2;
    } else if (preset === 'top') {
      camera.alpha = 0;
      camera.beta = 0.01;
    } else if (preset === 'front') {
      camera.alpha = -Math.PI / 2;
      camera.beta = Math.PI / 2.2;
    } else if (preset === 'reset') {
      camera.alpha = -Math.PI / 3;
      camera.beta = Math.PI / 3.2;
      if (BABYLON?.Vector3) {
        camera.target = new BABYLON.Vector3(0, 0, 0);
      }
    }
  };

  // Inspect Measurement Trace
  const handleInspectMeasurement = async (meas) => {
    setSelectedMeasurement(meas);
    setTraceLoading(true);
    setTraceData(null);
    try {
      if (jobId && cadModel && meas.id) {
        const trace = await cadApi.getCADTrace(jobId, cadModel.id, meas.id);
        setTraceData(trace);
      } else {
        setTraceData({
          measurement: {
            feature: meas.measurement_type.replace('_', ' ').title(),
            measured_value: meas.value,
            unit: meas.unit,
            axis: meas.axis,
          },
          source: {
            cad_model_id: cadModel?.id,
            evidence_id: cadModel?.evidence_id,
            sha256: cadModel?.model_hash,
            kernel_name: cadModel?.kernel_name,
          },
          geometry_reference: meas.source_reference,
          provenance_chain: 'Product DNA -> CAD Measurement -> Geometry Feature -> CAD Snapshot -> Evidence -> SHA-256',
        });
      }
    } catch (err) {
      console.warn('Failed to load measurement trace:', err);
    } finally {
      setTraceLoading(false);
    }
  };

  // Map to Product DNA
  const handleMapToDNA = async () => {
    if (!jobId || !cadModel) return;
    setMappingLoading(true);
    setMappingMessage(null);
    try {
      const res = await cadApi.mapCADToDNA(jobId, cadModel.id);
      setMappingMessage({ type: 'success', text: res.message });
      if (onMapToDNASuccess) onMapToDNASuccess(res);
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? detail.message : detail || err.message;
      setMappingMessage({
        type: 'error',
        text: msg || 'Failed to map CAD measurements to Product DNA.',
      });
    } finally {
      setMappingLoading(false);
    }
  };

  return (
    <div className="relative w-full h-[560px] bg-[#070A12] rounded-lg overflow-hidden border border-[#1E293B] shadow-inner flex flex-col">
      {/* Babylon 3D Canvas */}
      <canvas
        ref={canvasRef}
        id="babylonCanvas"
        className="w-full h-full block cursor-grab active:cursor-grabbing"
      />

      {/* Top HUD Bar */}
      <div className="absolute top-3 left-4 right-4 flex items-center justify-between pointer-events-none z-10">
        <div className="flex items-center gap-2 bg-[#0B132B]/90 backdrop-blur-md px-3 py-1.5 rounded border border-[#1E293B] pointer-events-auto">
          <span
            className={`w-2 h-2 rounded-full ${
              viewerState === 'CAD_READY'
                ? 'bg-emerald-400'
                : viewerState === 'CAD_PROCESSING'
                ? 'bg-amber-400 animate-ping'
                : viewerState === 'CAD_FAILED'
                ? 'bg-red-400'
                : 'bg-blue-500'
            }`}
          />
          <span className="font-mono text-[11px] font-semibold text-slate-200 tracking-wider">
            {cadModel
              ? `${cadModel.format} // ${cadModel.kernel_name}`
              : 'BABYLON.JS CAD TWIN // 3D VIEWPORT READY'}
          </span>
          {cadModel && (
            <span className="font-mono text-[10px] text-slate-400 border-l border-slate-700 pl-2">
              HASH: {cadModel.model_hash?.substring(0, 8)}...
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 pointer-events-auto">
          {viewerState === 'CAD_READY' && (
            <button
              type="button"
              onClick={handleMapToDNA}
              disabled={mappingLoading}
              className="px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-[11px] font-medium transition-colors flex items-center gap-1 shadow-sm"
              title="Populate authoritative Product DNA with verified CAD measurements"
            >
              <span className="material-symbols-outlined text-[14px]">fingerprint</span>
              {mappingLoading ? 'Mapping...' : 'Map to Product DNA'}
            </button>
          )}

          <div className="flex items-center gap-2 bg-[#0B132B]/90 backdrop-blur-md px-3 py-1.5 rounded border border-[#1E293B]">
            <span className="font-mono text-[10px] text-slate-400">STATE:</span>
            <span
              className={`font-mono text-[11px] font-semibold tracking-wider ${
                viewerState === 'CAD_READY'
                  ? 'text-emerald-400'
                  : viewerState === 'CAD_PROCESSING'
                  ? 'text-amber-400'
                  : viewerState === 'CAD_FAILED'
                  ? 'text-rose-400'
                  : 'text-blue-400'
              }`}
            >
              {viewerState}
            </span>
          </div>
        </div>
      </div>

      {/* Mapping Notification Toast */}
      {mappingMessage && (
        <div className="absolute top-14 left-4 right-4 z-20 flex justify-center pointer-events-none">
          <div
            className={`px-4 py-2 rounded-lg text-xs font-medium border shadow-lg pointer-events-auto flex items-center gap-2 ${
              mappingMessage.type === 'success'
                ? 'bg-emerald-950/90 text-emerald-200 border-emerald-700'
                : 'bg-rose-950/90 text-rose-200 border-rose-700'
            }`}
          >
            <span className="material-symbols-outlined text-sm">
              {mappingMessage.type === 'success' ? 'check_circle' : 'warning'}
            </span>
            <span>{mappingMessage.text}</span>
            <button
              type="button"
              onClick={() => setMappingMessage(null)}
              className="ml-2 text-slate-400 hover:text-white"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Empty State Overlay */}
      {viewerState === 'NO_CAD' && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
          <div className="bg-[#0B132B]/90 backdrop-blur-md border border-[#1E293B] rounded-lg p-6 max-w-md text-center pointer-events-auto shadow-2xl">
            <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-blue-950/60 border border-blue-800/40 flex items-center justify-center text-blue-400">
              <span className="material-symbols-outlined text-2xl">view_in_ar</span>
            </div>
            <h3 className="font-semibold text-white text-sm tracking-tight mb-1">
              Compile Compliance Viewport Ready
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed mb-4">
              Coordinate datum grid active. Upload a standard STEP CAD file (.stp, .step) to extract
              deterministic bounding box, wall thickness, hole diameters, and spatial clearance.
            </p>
            <div className="flex items-center justify-center gap-2">
              <button
                type="button"
                onClick={onUploadClick}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-medium transition-colors flex items-center gap-1.5 shadow-sm"
              >
                <span className="material-symbols-outlined text-sm">upload_file</span>
                Upload STEP CAD Model
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CAD Processing State */}
      {viewerState === 'CAD_PROCESSING' && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
          <div className="bg-[#0B132B]/95 backdrop-blur-md border border-amber-700/60 rounded-xl p-6 max-w-sm text-center shadow-2xl">
            <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-amber-950/60 border border-amber-600/40 flex items-center justify-center text-amber-400 shadow-[0_0_15px_rgba(245,158,11,0.2)]">
              <MorphingInfinity className="w-6 h-6 text-amber-400" />
            </div>
            <h3 className="font-semibold text-white text-sm tracking-tight mb-1">
              <TextShimmer baseColor="#f59e0b" shimmerColor="#fef08a" duration={2}>
                Parsing CAD Geometry...
              </TextShimmer>
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Extracting ISO 10303-21 B-Rep topology, computing bounding extents, and calculating
              deterministic physical dimensions.
            </p>
          </div>
        </div>
      )}

      {/* CAD Failed State */}
      {viewerState === 'CAD_FAILED' && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
          <div className="bg-[#0B132B]/95 backdrop-blur-md border border-rose-700/60 rounded-lg p-6 max-w-sm text-center shadow-2xl">
            <div className="w-10 h-10 mx-auto mb-3 rounded-full bg-rose-950/60 border border-rose-600/40 flex items-center justify-center text-rose-400">
              <span className="material-symbols-outlined text-xl">error</span>
            </div>
            <h3 className="font-semibold text-white text-sm tracking-tight mb-1">
              CAD Processing Failed
            </h3>
            <p className="text-xs text-rose-300 leading-relaxed mb-3">
              {cadModel?.error_message || 'Could not parse STEP geometry.'}
            </p>
            <button
              type="button"
              onClick={onUploadClick}
              className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-white rounded text-xs"
            >
              Try Another CAD File
            </button>
          </div>
        </div>
      )}

      {/* Geometry Trace Side Drawer */}
      {selectedMeasurement && (
        <div className="absolute top-12 right-4 bottom-16 w-80 bg-[#0B132B]/95 backdrop-blur-md border border-[#1E293B] rounded-lg p-4 z-30 shadow-2xl flex flex-col justify-between overflow-y-auto">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-700">
              <div className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-blue-400 text-sm">straighten</span>
                <span className="font-mono text-[11px] font-bold text-white uppercase tracking-wider">
                  CAD Measurement Trace
                </span>
              </div>
              <button
                type="button"
                onClick={() => setSelectedMeasurement(null)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            {traceLoading ? (
              <div className="py-8 text-center text-xs text-slate-400">Loading statutory trace...</div>
            ) : traceData ? (
              <div className="flex flex-col gap-2.5 mt-3 font-mono text-xs">
                <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase block">Feature</span>
                  <span className="font-bold text-white text-sm">
                    {traceData.measurement.feature}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase block">Measured</span>
                    <span className="font-bold text-emerald-400 text-sm">
                      {traceData.measurement.measured_value} {traceData.measurement.unit}
                    </span>
                  </div>
                  <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase block">Axis</span>
                    <span className="font-semibold text-slate-200 text-sm">
                      {traceData.measurement.axis || 'N/A'}
                    </span>
                  </div>
                </div>

                <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase block">Geometry Entity</span>
                  <span className="text-blue-300 font-semibold break-all text-[11px]">
                    {traceData.geometry_reference}
                  </span>
                </div>

                <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase block">Source Evidence</span>
                  <span className="text-slate-300 text-[11px] block">
                    {traceData.source.evidence_id}
                  </span>
                  <span className="text-[10px] text-slate-500 block truncate">
                    SHA: {traceData.source.sha256}
                  </span>
                </div>

                <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase block">Kernel Engine</span>
                  <span className="text-slate-300 text-[11px]">
                    {traceData.source.kernel_name} v{traceData.source.kernel_version}
                  </span>
                </div>

                <div className="p-2 bg-blue-950/40 border border-blue-900/60 rounded text-[10px] text-blue-200">
                  <span className="font-bold block mb-0.5">Authoritative Provenance:</span>
                  {traceData.provenance_chain}
                </div>
              </div>
            ) : null}
          </div>

          <button
            type="button"
            onClick={() => setSelectedMeasurement(null)}
            className="w-full py-1.5 mt-3 bg-slate-800 hover:bg-slate-700 text-white rounded text-xs transition-colors"
          >
            Close Trace
          </button>
        </div>
      )}

      {/* Bottom HUD Bar: Camera Presets & Live CAD Telemetry */}
      <div className="absolute bottom-3 left-4 right-4 flex items-center justify-between z-10 pointer-events-none">
        {/* Camera Preset Controls */}
        <div className="flex items-center gap-1 bg-[#0B132B]/90 backdrop-blur-md p-1 rounded border border-[#1E293B] pointer-events-auto">
          {['iso', 'ortho', 'top', 'front'].map((preset) => (
            <button
              key={preset}
              type="button"
              onClick={() => setCameraPreset(preset)}
              className={`px-2.5 py-1 rounded text-[11px] font-mono uppercase transition-colors ${
                activePreset === preset
                  ? 'bg-blue-600 text-white font-semibold'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              {preset}
            </button>
          ))}
          <div className="w-px h-3 bg-slate-700 mx-0.5" />
          <button
            type="button"
            onClick={() => setCameraPreset('reset')}
            title="Reset Camera"
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition-colors flex items-center"
          >
            <span className="material-symbols-outlined text-[14px]">restart_alt</span>
          </button>
        </div>

        {/* Live Measurements Carousel / Clickable Telemetry */}
        {measurements && measurements.length > 0 ? (
          <div className="hidden md:flex items-center gap-2 bg-[#0B132B]/90 backdrop-blur-md px-3 py-1.5 rounded border border-[#1E293B] pointer-events-auto overflow-x-auto max-w-xl">
            {measurements.slice(0, 4).map((m) => (
              <button
                key={m.id || m.measurement_type}
                type="button"
                onClick={() => handleInspectMeasurement(m)}
                className="flex items-center gap-1.5 text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900/60 hover:bg-blue-900/40 border border-slate-800 hover:border-blue-700 transition-colors text-left shrink-0"
                title="Click to view statutory CAD trace"
              >
                <span className="text-slate-400 text-[10px]">
                  {m.measurement_type.replace('BOUNDING_BOX_', 'DIM_').replace('_', ' ')}:
                </span>
                <span className="text-emerald-400 font-semibold">
                  {m.value} {m.unit}
                </span>
              </button>
            ))}
          </div>
        ) : (
          <div className="hidden sm:flex items-center gap-3 bg-[#0B132B]/90 backdrop-blur-md px-3 py-1.5 rounded border border-[#1E293B]">
            <div className="flex items-center gap-1.5 text-[11px] font-mono">
              <span className="text-slate-400">STATUS:</span>
              <span className="text-slate-300">AWAITING CAD GEOMETRY</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
