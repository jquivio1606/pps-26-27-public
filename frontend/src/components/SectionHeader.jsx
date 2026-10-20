export default function SectionHeader({ eyebrow, title, sub, id }) {
  return (
    <div className="ca-section-head" id={id}>
      {eyebrow && <p className="ca-eyebrow">◆ {eyebrow} ◆</p>}
      <h2 className="ca-section-title">{title}</h2>
      {sub && <p className="ca-section-sub">{sub}</p>}
    </div>
  );
}
