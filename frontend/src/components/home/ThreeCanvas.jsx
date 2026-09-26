import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

export default function ThreeCanvas({ onCanvasInteraction }) {
  const containerRef = useRef(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // 1. Scene & Atmosphere Setup (Authentic Indian Standards Directorate aesthetic)
    // Deep regal navy-slate with brass & warm gold accents
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x040814);
    scene.fog = new THREE.FogExp2(0x040814, 0.035);

    const camera = new THREE.PerspectiveCamera(
      42,
      window.innerWidth / window.innerHeight,
      0.1,
      100
    );
    camera.position.set(0, 0, 16.5);

    // 2. High-performance WebGL Renderer
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false,
      powerPreference: 'high-performance',
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    container.appendChild(renderer.domElement);

    // 3. Precision Industrial Lighting
    const ambientLight = new THREE.AmbientLight(0x131d36, 2.4);
    scene.add(ambientLight);

    // Warm brass key light
    const brassLight = new THREE.PointLight(0xf5b738, 4.0, 32);
    brassLight.position.set(5, 4, 6);
    scene.add(brassLight);

    // Cool calibration rim light
    const certBlueLight = new THREE.DirectionalLight(0x60a5fa, 1.8);
    certBlueLight.position.set(-6, -4, 5);
    scene.add(certBlueLight);

    // Emerald verification glow light
    const emeraldVerifyLight = new THREE.PointLight(0x10b981, 2.5, 20);
    emeraldVerifyLight.position.set(0, -3, 3);
    scene.add(emeraldVerifyLight);

    // 4. Central BIS Certification Mechanical Engine Group
    const bisRootGroup = new THREE.Group();
    scene.add(bisRootGroup);

    // --- A. Master BIS Certification Gear (24 Teeth Ashok/Industrial Standard Cog) ---
    const gearGroup = new THREE.Group();
    bisRootGroup.add(gearGroup);

    // Machined brass material for BIS standard wheel
    const brassMaterial = new THREE.MeshStandardMaterial({
      color: 0xdfa037,
      metalness: 0.88,
      roughness: 0.28,
      emissive: 0x784e10,
      emissiveIntensity: 0.25,
    });

    const darkSteelMaterial = new THREE.MeshStandardMaterial({
      color: 0x1f293d,
      metalness: 0.92,
      roughness: 0.2,
      wireframe: false,
    });

    const goldenWireMaterial = new THREE.MeshBasicMaterial({
      color: 0xf59e0b,
      wireframe: true,
      transparent: true,
      opacity: 0.4,
    });

    // Outer Gear Rim
    const rimRadius = 4.1;
    const rimTube = 0.12;
    const rimGeo = new THREE.TorusGeometry(rimRadius, rimTube, 20, 120);
    const rimMesh = new THREE.Mesh(rimGeo, brassMaterial);
    gearGroup.add(rimMesh);

    // 24 Machined Cog Teeth around the circumference (BIS Standard Gear)
    const teethCount = 24;
    const toothGeo = new THREE.BoxGeometry(0.28, 0.45, 0.22);
    for (let i = 0; i < teethCount; i++) {
      const angle = (i * Math.PI * 2) / teethCount;
      const tooth = new THREE.Mesh(toothGeo, brassMaterial);
      tooth.position.set(
        Math.cos(angle) * (rimRadius + 0.15),
        Math.sin(angle) * (rimRadius + 0.15),
        0
      );
      tooth.rotation.z = angle;
      gearGroup.add(tooth);
    }

    // Concentric Calibration Dial Ring with Micrometer Gauge Divisions
    const dialRingGeo = new THREE.RingGeometry(3.0, 3.8, 64);
    // Draw calibration tick marks on a circular canvas texture
    const dialCanvas = document.createElement('canvas');
    dialCanvas.width = 1024;
    dialCanvas.height = 1024;
    const dctx = dialCanvas.getContext('2d');
    if (dctx) {
      dctx.clearRect(0, 0, 1024, 1024);
      dctx.strokeStyle = '#dfa037';
      dctx.lineWidth = 3;

      // Draw concentric guide lines
      dctx.beginPath();
      dctx.arc(512, 512, 480, 0, Math.PI * 2);
      dctx.stroke();

      dctx.beginPath();
      dctx.arc(512, 512, 420, 0, Math.PI * 2);
      dctx.stroke();

      // Draw 72 graduation ticks (standards calibration)
      for (let t = 0; t < 72; t++) {
        const rad = (t * Math.PI * 2) / 72;
        const isMajor = t % 6 === 0;
        const rInner = isMajor ? 410 : 440;
        const rOuter = 480;

        dctx.lineWidth = isMajor ? 5 : 2;
        dctx.strokeStyle = isMajor ? '#f59e0b' : 'rgba(223, 160, 55, 0.5)';
        dctx.beginPath();
        dctx.moveTo(512 + Math.cos(rad) * rInner, 512 + Math.sin(rad) * rInner);
        dctx.lineTo(512 + Math.cos(rad) * rOuter, 512 + Math.sin(rad) * rOuter);
        dctx.stroke();
      }

      // Add text stamping along dial
      dctx.fillStyle = '#f59e0b';
      dctx.font = 'bold 22px monospace';
      dctx.textAlign = 'center';
      dctx.fillText('BUREAU OF INDIAN STANDARDS • CONFORMITY AUDIT GAUGE • IS 16', 512, 50);
    }
    const dialTexture = new THREE.CanvasTexture(dialCanvas);
    const dialMat = new THREE.MeshBasicMaterial({
      map: dialTexture,
      transparent: true,
      side: THREE.DoubleSide,
      opacity: 0.65,
    });
    const dialMesh = new THREE.Mesh(dialRingGeo, dialMat);
    gearGroup.add(dialMesh);

    // Inner Concentric Spoke System (6 Heavy Machined Spokes)
    for (let s = 0; s < 6; s++) {
      const angle = (s * Math.PI * 2) / 6;
      const spokeGeo = new THREE.CylinderGeometry(0.06, 0.06, 3.8, 12);
      const spokeMesh = new THREE.Mesh(spokeGeo, brassMaterial);
      spokeMesh.position.set(
        Math.cos(angle) * 1.9,
        Math.sin(angle) * 1.9,
        0
      );
      spokeMesh.rotation.z = angle + Math.PI / 2;
      gearGroup.add(spokeMesh);
    }

    // --- B. Central ISI Standard Mark Medallion / Embossed Stamp ---
    const stampGroup = new THREE.Group();
    bisRootGroup.add(stampGroup);

    // Central circular steel hub
    const hubGeo = new THREE.CylinderGeometry(1.6, 1.6, 0.35, 64);
    hubGeo.rotateX(Math.PI / 2);
    const hubMesh = new THREE.Mesh(hubGeo, darkSteelMaterial);
    stampGroup.add(hubMesh);

    // Golden embossed border ring for central ISI medallion
    const hubBorderGeo = new THREE.TorusGeometry(1.6, 0.08, 16, 64);
    const hubBorderMesh = new THREE.Mesh(hubBorderGeo, brassMaterial);
    stampGroup.add(hubBorderMesh);

    // Authentic ISI Logo & "मानक: पथप्रदर्शक:" BIS Motto Canvas Stamp
    const stampCanvas = document.createElement('canvas');
    stampCanvas.width = 512;
    stampCanvas.height = 512;
    const sctx = stampCanvas.getContext('2d');
    if (sctx) {
      sctx.fillStyle = '#080e1c';
      sctx.beginPath();
      sctx.arc(256, 256, 250, 0, Math.PI * 2);
      sctx.fill();

      // Border in gold
      sctx.strokeStyle = '#f5b738';
      sctx.lineWidth = 10;
      sctx.stroke();

      sctx.lineWidth = 3;
      sctx.beginPath();
      sctx.arc(256, 256, 226, 0, Math.PI * 2);
      sctx.stroke();

      // Draw stylized ISI mark geometry
      sctx.fillStyle = '#f5b738';
      sctx.textAlign = 'center';
      sctx.textBaseline = 'middle';

      // "ISI" Bold Official Monogram
      sctx.font = '900 86px serif';
      sctx.fillText('ISI', 256, 230);

      // Top arc label
      sctx.font = '600 24px sans-serif';
      sctx.fillText('B I S', 256, 125);

      // Bottom legal standard label
      sctx.font = '500 20px monospace';
      sctx.fillText('STANDARD MARK', 256, 320);
      sctx.font = '400 15px sans-serif';
      sctx.fillStyle = '#94a3b8';
      sctx.fillText('GOVT. OF INDIA', 256, 355);

      // Verification checkmark emblem
      sctx.strokeStyle = '#10b981';
      sctx.lineWidth = 6;
      sctx.beginPath();
      sctx.moveTo(215, 395);
      sctx.lineTo(245, 425);
      sctx.lineTo(300, 375);
      sctx.stroke();
    }
    const stampTexture = new THREE.CanvasTexture(stampCanvas);
    const stampPlaneGeo = new THREE.CircleGeometry(1.5, 48);
    const stampPlaneMat = new THREE.MeshBasicMaterial({
      map: stampTexture,
      transparent: true,
      side: THREE.DoubleSide,
    });
    const stampPlaneMesh = new THREE.Mesh(stampPlaneGeo, stampPlaneMat);
    stampPlaneMesh.position.z = 0.18;
    stampGroup.add(stampPlaneMesh);

    // --- C. Floating Dynamic Standards Hologram Nodes in 3D Space ---
    const standardsData = [
      { code: 'IS 13252', label: 'Electronics Safety', color: '#60a5fa' },
      { code: 'IS 16046', label: 'Lithium Battery CRS', color: '#38bdf8' },
      { code: 'IS 9873', label: 'Toy Safety (Mandatory)', color: '#f59e0b' },
      { code: 'IS 4151', label: 'Protective Helmets ISI', color: '#10b981' },
      { code: 'IS 14543', label: 'Drinking Water QCO', color: '#38bdf8' },
      { code: 'IS 1786', label: 'TMT Steel Rebars', color: '#f97316' },
      { code: 'IS 1417', label: 'Gold Hallmarking HUID', color: '#eab308' },
      { code: 'IS 302', label: 'Electrical Appliances', color: '#a855f7' },
    ];

    const badgeMeshes = [];
    const orbitRadius = 6.2;

    standardsData.forEach((std) => {
      const bCanvas = document.createElement('canvas');
      bCanvas.width = 320;
      bCanvas.height = 100;
      const bctx = bCanvas.getContext('2d');
      if (bctx) {
        bctx.fillStyle = 'rgba(7, 16, 38, 0.88)';
        bctx.roundRect(4, 4, 312, 92, 16);
        bctx.fill();

        bctx.strokeStyle = std.color;
        bctx.lineWidth = 3;
        bctx.roundRect(4, 4, 312, 92, 16);
        bctx.stroke();

        bctx.fillStyle = '#ffffff';
        bctx.font = 'bold 28px monospace';
        bctx.textAlign = 'left';
        bctx.fillText(std.code, 22, 42);

        bctx.fillStyle = std.color;
        bctx.font = '600 16px sans-serif';
        bctx.fillText(std.label, 22, 74);

        bctx.fillStyle = '#10b981';
        bctx.beginPath();
        bctx.arc(285, 48, 8, 0, Math.PI * 2);
        bctx.fill();
      }

      const bTex = new THREE.CanvasTexture(bCanvas);
      const bMat = new THREE.MeshBasicMaterial({
        map: bTex,
        transparent: true,
        side: THREE.DoubleSide,
      });
      const bGeo = new THREE.PlaneGeometry(1.6, 0.5);
      const bMesh = new THREE.Mesh(bGeo, bMat);

      bisRootGroup.add(bMesh);
      badgeMeshes.push(bMesh);
    });

    // --- D. Laser Verification Sweep Line Geometry ---
    const scanLineGeo = new THREE.PlaneGeometry(10.5, 0.05);
    const scanLineMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.6,
      side: THREE.DoubleSide,
    });
    const scanLine = new THREE.Mesh(scanLineGeo, scanLineMat);
    scanLine.position.z = 0.5;
    bisRootGroup.add(scanLine);

    // --- E. Ambient Atmospheric Depth Particles (Quality & Conformity Dust) ---
    const particleCount = 280;
    const particleGeo = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);
    const particleBasePos = new Float32Array(particleCount * 3);

    for (let p = 0; p < particleCount; p++) {
      const px = (Math.random() - 0.5) * 36;
      const py = (Math.random() - 0.5) * 24;
      const pz = (Math.random() - 0.5) * 16 - 2;

      particlePositions[p * 3] = px;
      particlePositions[p * 3 + 1] = py;
      particlePositions[p * 3 + 2] = pz;

      particleBasePos[p * 3] = px;
      particleBasePos[p * 3 + 1] = py;
      particleBasePos[p * 3 + 2] = pz;
    }

    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));

    const pCanvas = document.createElement('canvas');
    pCanvas.width = 64;
    pCanvas.height = 64;
    const pctx = pCanvas.getContext('2d');
    if (pctx) {
      const grad = pctx.createRadialGradient(32, 32, 0, 32, 32, 32);
      grad.addColorStop(0, 'rgba(245, 183, 56, 1)');
      grad.addColorStop(0.3, 'rgba(56, 189, 248, 0.7)');
      grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
      pctx.fillStyle = grad;
      pctx.beginPath();
      pctx.arc(32, 32, 32, 0, Math.PI * 2);
      pctx.fill();
    }
    const particleTex = new THREE.CanvasTexture(pCanvas);
    const particleMat = new THREE.PointsMaterial({
      size: 0.28,
      map: particleTex,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);

    // 5. Interactive Mouse Parallax & Inertia
    let mouseX = 0;
    let mouseY = 0;
    let targetMouseX = 0;
    let targetMouseY = 0;
    let isMouseDown = false;
    let gearExtraSpin = 0;

    const onPointerMove = (e) => {
      targetMouseX = (e.clientX / window.innerWidth) * 2 - 1;
      targetMouseY = -(e.clientY / window.innerHeight) * 2 + 1;
    };

    const onPointerDown = () => {
      isMouseDown = true;
      gearExtraSpin += 0.25;
      if (onCanvasInteraction) onCanvasInteraction();
    };

    const onPointerUp = () => {
      isMouseDown = false;
    };

    const onTouchMove = (e) => {
      if (e.touches.length > 0) {
        targetMouseX = (e.touches[0].clientX / window.innerWidth) * 2 - 1;
        targetMouseY = -(e.touches[0].clientY / window.innerHeight) * 2 + 1;
      }
    };

    window.addEventListener('mousemove', onPointerMove, { passive: true });
    window.addEventListener('mousedown', onPointerDown);
    window.addEventListener('mouseup', onPointerUp);
    window.addEventListener('touchmove', onTouchMove, { passive: true });

    // Responsive Canvas Resizing
    const onResize = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      camera.aspect = w / h;

      if (w < 768) {
        camera.position.z = 21;
      } else {
        camera.position.z = 16.5;
      }

      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    };

    onResize();
    window.addEventListener('resize', onResize);

    // 6. Smooth Animation Loop
    let animationFrameId;
    const clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Damped pointer follow
      mouseX += (targetMouseX - mouseX) * 0.04;
      mouseY += (targetMouseY - mouseY) * 0.04;
      gearExtraSpin *= 0.94; // friction decay

      // Rotate Master BIS Gear (mechanical, steady clockwork precision)
      gearGroup.rotation.z = -(elapsedTime * 0.12 + gearExtraSpin);
      
      // Central ISI stamp breathes and gently tilts
      stampGroup.rotation.z = Math.sin(elapsedTime * 0.4) * 0.05;
      const stampPulse = 1.0 + Math.sin(elapsedTime * 2.0) * 0.02;
      stampGroup.scale.set(stampPulse, stampPulse, stampPulse);

      // Move Laser Verification Scan across the certification dial
      const scanY = Math.sin(elapsedTime * 1.6) * 4.2;
      scanLine.position.y = scanY;
      scanLine.scale.x = Math.max(0.2, Math.cos((scanY / 4.2) * (Math.PI / 2.2)));

      // Orbit the real IS code badges around the central gear
      const badgeCount = badgeMeshes.length;
      for (let i = 0; i < badgeCount; i++) {
        const badge = badgeMeshes[i];
        const theta = elapsedTime * 0.15 + (i * Math.PI * 2) / badgeCount;
        const bx = Math.cos(theta) * orbitRadius;
        const by = Math.sin(theta) * (orbitRadius * 0.55); // slight perspective ellipse
        const bz = Math.sin(theta) * 1.5;

        badge.position.set(bx, by, bz);
        // Badges always face towards the camera with gentle tilt
        badge.rotation.x = -mouseY * 0.2;
        badge.rotation.y = mouseX * 0.2;
        badge.rotation.z = Math.sin(elapsedTime + i) * 0.05;
      }

      // Parallax 3D tilt of the entire BIS engine based on cursor
      bisRootGroup.rotation.y = mouseX * 0.35;
      bisRootGroup.rotation.x = -mouseY * 0.25;
      bisRootGroup.position.y = Math.sin(elapsedTime * 0.6) * 0.18;

      camera.position.x = mouseX * 0.8;
      camera.position.y = mouseY * 0.5;
      camera.lookAt(0, 0, 0);

      // Light oscillation
      brassLight.position.x = 5 + Math.sin(elapsedTime * 1.2) * 1.5;
      brassLight.position.y = 4 + Math.cos(elapsedTime * 1.5) * 1.5;

      // Particle drift
      const pArr = particleGeo.attributes.position.array;
      for (let i = 0; i < particleCount; i++) {
        const idx = i * 3;
        const ox = particleBasePos[idx];
        const oy = particleBasePos[idx + 1];
        const oz = particleBasePos[idx + 2];
        pArr[idx] = ox + Math.sin(elapsedTime * 0.4 + oy) * 0.15;
        pArr[idx + 1] = oy + Math.cos(elapsedTime * 0.3 + ox) * 0.15;
        pArr[idx + 2] = oz + Math.sin(elapsedTime * 0.2 + oz) * 0.1;
      }
      particleGeo.attributes.position.needsUpdate = true;

      renderer.render(scene, camera);
    };

    animate();

    // 7. Cleanup
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('mousemove', onPointerMove);
      window.removeEventListener('mousedown', onPointerDown);
      window.removeEventListener('mouseup', onPointerUp);
      window.removeEventListener('touchmove', onTouchMove);
      window.removeEventListener('resize', onResize);

      rimGeo.dispose();
      toothGeo.dispose();
      dialRingGeo.dispose();
      dialTexture.dispose();
      hubGeo.dispose();
      hubBorderGeo.dispose();
      stampPlaneGeo.dispose();
      stampTexture.dispose();
      scanLineGeo.dispose();
      particleGeo.dispose();
      particleTex.dispose();

      brassMaterial.dispose();
      darkSteelMaterial.dispose();
      goldenWireMaterial.dispose();
      dialMat.dispose();
      stampPlaneMat.dispose();
      scanLineMat.dispose();
      particleMat.dispose();

      badgeMeshes.forEach((mesh) => {
        mesh.geometry.dispose();
        mesh.material.dispose();
      });

      renderer.dispose();
      if (container && renderer.domElement) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [onCanvasInteraction]);

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 w-full h-full pointer-events-auto cursor-grab active:cursor-grabbing z-0"
      aria-hidden="true"
    />
  );
}
