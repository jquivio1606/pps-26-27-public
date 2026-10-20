/**
 * Bus de eventos mínimo para avisar a las páginas de que los datos
 * han cambiado (por ejemplo, tras una compra o al crear en admin).
 */

const listeners = new Set();

export function onDataChanged(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

export function emitDataChanged() {
  listeners.forEach((fn) => fn());
}
