import type { ReactNode } from 'react';
import { motion } from 'framer-motion';
import type { ResolvedRelation } from '@/types';
import { useSelectionDetail } from '@/hooks/useSelection';
import { useActions } from '@/app/store';
import { entityProperties } from '@/utils/properties';
import { presentEntity } from '@/utils/present';
import { ENTITY_BY_ID } from '@/data';
import { KIND_LABEL, RELATION_LABEL } from '@/data/labels';
import { Icon } from '@/components/ui/Icon';
import { ConfidenceTag } from '@/components/ui/ConfidenceTag';
import { IconButton } from '@/components/ui/IconButton';

/** Инспектор — главный способ изучения системы: свойства, связи, правила, решения, история. */
export function Inspector() {
  const detail = useSelectionDetail();
  const actions = useActions();
  if (!detail) return null;

  const { entity, incoming, outgoing, rules, decisions } = detail;
  const { iconKey, color } = presentEntity(entity);
  const props = entityProperties(entity);

  // Запреты, относящиеся к выбранной сущности.
  const forbiddenRows: { title: string; reason: string }[] = [];
  if (entity.kind === 'traffic_source') {
    for (const r of rules) {
      if (!r.sourceIds.includes(entity.id)) continue;
      for (const f of r.forbidden) {
        forbiddenRows.push({ title: `→ ${ENTITY_BY_ID.get(f.landingId)?.code ?? f.landingId}`, reason: f.reason });
      }
    }
  } else if (entity.kind === 'landing') {
    for (const r of rules) {
      for (const f of r.forbidden) {
        if (f.landingId === entity.id) {
          forbiddenRows.push({ title: `${r.sourceIds.map((s) => ENTITY_BY_ID.get(s)?.code ?? s).join(' / ')} →`, reason: f.reason });
        }
      }
    }
  }

  return (
    <motion.aside
      className="panel inspector"
      initial={{ x: 24, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 24, opacity: 0 }}
      transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className="inspector__close">
        <IconButton icon="x" title="Закрыть" ghost onClick={() => actions.select(null)} />
      </div>

      <div className="inspector__head">
        <div className="inspector__kind">
          <span className="node__icon" style={{ background: color.soft, color: color.accent, width: 22, height: 22 }}>
            <Icon name={iconKey} size={13} />
          </span>
          {KIND_LABEL[entity.kind]}
        </div>
        <div className="inspector__code">{entity.code}</div>
        <div className="inspector__name">{entity.name}</div>
        {(entity.confidence || entity.kind === 'cell') && (
          <div style={{ marginTop: 8, display: 'flex', gap: 6 }}>
            {entity.confidence && <ConfidenceTag confidence={entity.confidence} />}
          </div>
        )}
        {entity.description && <p className="inspector__desc">{entity.description}</p>}
      </div>

      <div className="inspector__body">
        <Section title="Свойства">
          {props.map((p) => (
            <div className="prop" key={p.k}>
              <span className="prop__k">{p.k}</span>
              <span className="prop__v">{p.v}</span>
            </div>
          ))}
        </Section>

        {entity.kind === 'contractor' && (
          <>
            <Section title="Поля ТЗ">
              {entity.fields.map((f) => (
                <div className="prop" key={f.key}>
                  <span className="prop__k">{f.label}</span>
                  <span className="prop__v">{f.value}</span>
                </div>
              ))}
            </Section>
            <Section title="Запреты">
              {entity.prohibitions.map((p, i) => (
                <div className="forbidden-row" key={i}>
                  <span className="forbidden-row__x">✕</span>
                  <span className="forbidden-row__body">{p}</span>
                </div>
              ))}
            </Section>
          </>
        )}

        {forbiddenRows.length > 0 && (
          <Section title="Запрещённые связи">
            {forbiddenRows.map((f, i) => (
              <div className="forbidden-row" key={i}>
                <span className="forbidden-row__x">✕</span>
                <div>
                  <div className="forbidden-row__t">{f.title}</div>
                  <div className="forbidden-row__r">{f.reason}</div>
                </div>
              </div>
            ))}
          </Section>
        )}

        {outgoing.length > 0 && (
          <Section title={`Исходящие связи · ${outgoing.length}`}>
            {outgoing.map((r) => (
              <RelationRow key={r.edge.id} rel={r} onOpen={() => actions.focus(r.node.id)} />
            ))}
          </Section>
        )}

        {incoming.length > 0 && (
          <Section title={`Входящие связи · ${incoming.length}`}>
            {incoming.map((r) => (
              <RelationRow key={r.edge.id} rel={r} onOpen={() => actions.focus(r.node.id)} />
            ))}
          </Section>
        )}

        {rules.length > 0 && entity.kind !== 'contractor' && (
          <Section title={`Правила · ${rules.length}`}>
            {rules.map((r) => (
              <div className="rel" key={r.id} onClick={() => actions.focus(r.id)}>
                <Icon name="sliders" size={13} color="#0ea5e9" />
                <span className="rel__name">{r.name}</span>
                <span className="rel__code">{r.code}</span>
              </div>
            ))}
          </Section>
        )}

        {decisions.length > 0 && (
          <Section title={`Связанные решения · ${decisions.length}`}>
            {decisions.map((d) => (
              <div className="rel" key={d.id} onClick={() => actions.focus(d.id)}>
                <Icon name="gauge" size={13} color="#f43f5e" />
                <span className="rel__name">{d.actionLabel}</span>
                {d.hypothesis && <span className="rel__label" style={{ color: '#f43f5e' }}>гипотеза</span>}
              </div>
            ))}
          </Section>
        )}

        <Section title="История изменений">
          {entity.history && entity.history.length > 0 ? (
            entity.history.map((h, i) => (
              <div className="prop" key={i}>
                <span className="prop__k">{h.date}</span>
                <span className="prop__v">{h.summary} · {h.author}</span>
              </div>
            ))
          ) : (
            <p className="muted" style={{ fontSize: 12, lineHeight: 1.5 }}>
              Структура истории предусмотрена — записей пока нет. Здесь появятся правки объекта с датой и автором.
            </p>
          )}
        </Section>
      </div>
    </motion.aside>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="section">
      <div className="section__title">{title}</div>
      {children}
    </div>
  );
}

function RelationRow({ rel, onOpen }: { rel: ResolvedRelation; onOpen: () => void }) {
  const entity = rel.node.entity;
  return (
    <div className="rel" onClick={onOpen}>
      <span className="rel__arrow">{rel.direction === 'outgoing' ? '→' : '←'}</span>
      <span className="rel__label">{RELATION_LABEL[rel.edge.type]}</span>
      <span className="rel__name">{entity?.name ?? rel.node.id}</span>
      <span className="rel__code">{entity?.code}</span>
    </div>
  );
}
