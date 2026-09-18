/**
 * Zyntrix Product DNA Domain Types & Section Definitions.
 * 
 * Enforces Cardinal Non-Negotiables:
 * 1. ONLY Accepted Evidence may contribute to Product DNA.
 * 2. Every parameter retains complete source provenance and SHA-256 integrity.
 * 3. Conflicting values require mandatory human engineering resolution.
 * 4. Product DNA is factual technical data, NOT a compliance certification.
 */

export const DNASection = {
  PRODUCT_IDENTITY: {
    id: 'PRODUCT_IDENTITY',
    title: 'Product Identity',
    icon: 'badge',
    description: 'Statutory model name, trade identification, manufacturer legal entity, and manufacturing facility.',
  },
  ELECTRICAL_CHARACTERISTICS: {
    id: 'ELECTRICAL_CHARACTERISTICS',
    title: 'Electrical Characteristics',
    icon: 'bolt',
    description: 'Voltage, current, frequency, power wattage, phase configuration, and insulation classification.',
  },
  MECHANICAL_CHARACTERISTICS: {
    id: 'MECHANICAL_CHARACTERISTICS',
    title: 'Mechanical Characteristics',
    icon: 'square_foot',
    description: 'Enclosure dimensions, chassis mass, ingress protection (IP code), wall thickness, and mounting.',
  },
  SAFETY_CHARACTERISTICS: {
    id: 'SAFETY_CHARACTERISTICS',
    title: 'Safety Characteristics',
    icon: 'verified_user',
    description: 'Spatial creepage, clearance distances, PE grounding continuity, and dielectric withstand thresholds.',
  },
  ENVIRONMENTAL_CHARACTERISTICS: {
    id: 'ENVIRONMENTAL_CHARACTERISTICS',
    title: 'Environmental Characteristics',
    icon: 'thermostat',
    description: 'Operating and storage temperature bounds, relative humidity limits, and maximum operating altitude.',
  },
  COMPONENTS: {
    id: 'COMPONENTS',
    title: 'Components & Critical Parts (CCL)',
    icon: 'memory',
    description: 'Critical Component List: power semiconductors, isolation transformers, filter capacitors, and fuses.',
  },
  MATERIALS: {
    id: 'MATERIALS',
    title: 'Materials & Enclosure Polymers',
    icon: 'category',
    description: 'Enclosure polymer flame retardancy (UL94), FR4 PCB substrates, and metallic conductor alloys.',
  },
  INTERFACES: {
    id: 'INTERFACES',
    title: 'Interfaces & Terminations',
    icon: 'cable',
    description: 'AC mains inlets, DC bus high-voltage terminals, communication ports, and earth grounding studs.',
  },
  REGULATORY_METADATA: {
    id: 'REGULATORY_METADATA',
    title: 'Regulatory Metadata',
    icon: 'gavel',
    description: 'Target BIS standard number, product category scope, gazetted QCO order, and registration scheme.',
  },
};

export const CANONICAL_PARAMETERS = [
  // Product Identity
  { id: 'PARAM-IDENT-01', section: 'PRODUCT_IDENTITY', name: 'Product Model / SKU', defaultUnit: '' },
  { id: 'PARAM-IDENT-02', section: 'PRODUCT_IDENTITY', name: 'Trade / Brand Name', defaultUnit: '' },
  { id: 'PARAM-IDENT-03', section: 'PRODUCT_IDENTITY', name: 'Manufacturer Legal Entity', defaultUnit: '' },
  { id: 'PARAM-IDENT-04', section: 'PRODUCT_IDENTITY', name: 'Country of Origin', defaultUnit: '' },
  { id: 'PARAM-IDENT-05', section: 'PRODUCT_IDENTITY', name: 'Manufacturing Facility Address', defaultUnit: '' },

  // Electrical Characteristics
  { id: 'PARAM-ELEC-01', section: 'ELECTRICAL_CHARACTERISTICS', name: 'Nominal Supply Voltage', defaultUnit: 'V' },
  { id: 'PARAM-ELEC-02', section: 'ELECTRICAL_CHARACTERISTICS', name: 'Rated Frequency', defaultUnit: 'Hz' },
  { id: 'PARAM-ELEC-03', section: 'ELECTRICAL_CHARACTERISTICS', name: 'Rated Input Current', defaultUnit: 'A' },
  { id: 'PARAM-ELEC-04', section: 'ELECTRICAL_CHARACTERISTICS', name: 'Rated Active Power', defaultUnit: 'W' },
  { id: 'PARAM-ELEC-05', section: 'ELECTRICAL_CHARACTERISTICS', name: 'Supply Phase Configuration', defaultUnit: '' },
  { id: 'PARAM-ELEC-06', section: 'ELECTRICAL_CHARACTERISTICS', name: 'Electric Shock Protection Class', defaultUnit: '' },

  // Mechanical Characteristics
  { id: 'PARAM-MECH-01', section: 'MECHANICAL_CHARACTERISTICS', name: 'Overall Physical Dimensions (W x H x D)', defaultUnit: 'mm' },
  { id: 'PARAM-MECH-02', section: 'MECHANICAL_CHARACTERISTICS', name: 'Chassis Net Mass', defaultUnit: 'kg' },
  { id: 'PARAM-MECH-03', section: 'MECHANICAL_CHARACTERISTICS', name: 'Ingress Protection Code (IP Rating)', defaultUnit: '' },
  { id: 'PARAM-MECH-04', section: 'MECHANICAL_CHARACTERISTICS', name: 'Primary Enclosure Material', defaultUnit: '' },
  { id: 'PARAM-MECH-05', section: 'MECHANICAL_CHARACTERISTICS', name: 'Minimum Enclosure Wall Thickness', defaultUnit: 'mm' },

  // Safety Characteristics
  { id: 'PARAM-SAFE-01', section: 'SAFETY_CHARACTERISTICS', name: 'Measured Creepage Distance (Primary to Ground)', defaultUnit: 'mm' },
  { id: 'PARAM-SAFE-02', section: 'SAFETY_CHARACTERISTICS', name: 'Measured Clearance Distance (Primary to PE)', defaultUnit: 'mm' },
  { id: 'PARAM-SAFE-03', section: 'SAFETY_CHARACTERISTICS', name: 'Protective Earth Resistance', defaultUnit: 'mΩ' },
  { id: 'PARAM-SAFE-04', section: 'SAFETY_CHARACTERISTICS', name: 'Dielectric Insulation Voltage', defaultUnit: 'Vrms' },
  { id: 'PARAM-SAFE-05', section: 'SAFETY_CHARACTERISTICS', name: 'Polymer Flammability Rating', defaultUnit: '' },

  // Environmental Characteristics
  { id: 'PARAM-ENV-01', section: 'ENVIRONMENTAL_CHARACTERISTICS', name: 'Operating Ambient Temperature Range', defaultUnit: '°C' },
  { id: 'PARAM-ENV-02', section: 'ENVIRONMENTAL_CHARACTERISTICS', name: 'Storage Temperature Range', defaultUnit: '°C' },
  { id: 'PARAM-ENV-03', section: 'ENVIRONMENTAL_CHARACTERISTICS', name: 'Maximum Relative Humidity (Non-condensing)', defaultUnit: '%' },
  { id: 'PARAM-ENV-04', section: 'ENVIRONMENTAL_CHARACTERISTICS', name: 'Maximum Operating Altitude', defaultUnit: 'm' },

  // Components (Critical Component List)
  { id: 'PARAM-COMP-01', section: 'COMPONENTS', name: 'Primary Power Switching Semiconductor', defaultUnit: '' },
  { id: 'PARAM-COMP-02', section: 'COMPONENTS', name: 'Main High-Frequency Isolation Transformer', defaultUnit: '' },
  { id: 'PARAM-COMP-03', section: 'COMPONENTS', name: 'DC Bus Bulk Electrolytic Capacitors', defaultUnit: '' },
  { id: 'PARAM-COMP-04', section: 'COMPONENTS', name: 'Input Overcurrent Protection Fuse Rating', defaultUnit: 'A' },

  // Materials
  { id: 'PARAM-MAT-01', section: 'MATERIALS', name: 'Enclosure Polymer Resin & Grade', defaultUnit: '' },
  { id: 'PARAM-MAT-02', section: 'MATERIALS', name: 'Printed Circuit Board Laminate Type', defaultUnit: '' },
  { id: 'PARAM-MAT-03', section: 'MATERIALS', name: 'Internal Wiring Insulation Specification', defaultUnit: '' },

  // Interfaces
  { id: 'PARAM-INT-01', section: 'INTERFACES', name: 'AC Mains Terminal Connection Type', defaultUnit: '' },
  { id: 'PARAM-INT-02', section: 'INTERFACES', name: 'DC Input Terminal Specification', defaultUnit: '' },
  { id: 'PARAM-INT-03', section: 'INTERFACES', name: 'Communication & Telemetry Interfaces', defaultUnit: '' },

  // Regulatory Metadata
  { id: 'PARAM-REG-01', section: 'REGULATORY_METADATA', name: 'Governing Indian Standard (IS)', defaultUnit: '' },
  { id: 'PARAM-REG-02', section: 'REGULATORY_METADATA', name: 'Statutory Product Category', defaultUnit: '' },
  { id: 'PARAM-REG-03', section: 'REGULATORY_METADATA', name: 'Compulsory Registration Scheme (CRS) Status', defaultUnit: '' },
];

export const ParameterReviewStatus = {
  ACCEPTED_EVIDENCE_BACKED: 'ACCEPTED_EVIDENCE_BACKED',
  CONFLICTING: 'CONFLICTING',
  ENGINEER_RESOLVED: 'ENGINEER_RESOLVED',
};
