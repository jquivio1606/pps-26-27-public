import { useToast } from "../context/ToastContext";

export default function ToastStack() {
  const { toasts, remove } = useToast();

  return (
    <div className="ca-toast-wrap" aria-live="polite" aria-atomic="true">
      {toasts.map((t) => (
        <div key={t.id} className={`ca-toast ${t.type}`} role="status" onClick={() => remove(t.id)}>
          <b>{t.title}</b>
          {t.message ? <span>{t.message}</span> : null}
        </div>
      ))}
    </div>
  );
}
