
const obj = {
  rawAttributes: {},
};
const dnaRows = Object.entries(obj.rawAttributes).map(([key, val]) => ({
  spec: key.replace(/_/g, ' ').toUpperCase(),
  value: String(val)
}));
