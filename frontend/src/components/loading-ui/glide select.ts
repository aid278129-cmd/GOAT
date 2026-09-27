## Integrate the < GlideSelect /> component from React Bits

You are helping integrate an open - source React component into an existing application.

### Component: GlideSelect
### Variant: JavaScript + CSS
### Dependencies: @hugeicons/react @hugeicons/core - free - icons

---

### Usage Example
    ```jsx
import GlideSelect from './GlideSelect';

const formats = [
  { value: 'png', label: 'PNG', tag: 'Lossless' },
  { value: 'jpg', label: 'JPG', tag: 'Smallest' },
  { value: 'webp', label: 'WebP', tag: 'Modern' },
  { value: 'svg', label: 'SVG', tag: 'Vector' },
  { value: 'pdf', label: 'PDF', tag: 'Print' }
];

<GlideSelect
  options={formats}
  defaultValue="png"
  onChange={(value, option) => console.log(value, option)}
  ariaLabel="Export format"
  showTags
  accentColor="#f5f5f5"
  surfaceColor="#27272a"
  highlightColor="#3f3f46"
  textColor="#f5f5f5"
  size="md"
  radius={10}
  menuWidth={176}
  placement="bottom"
  align="left"
  popDuration={180}
  glideDuration={220}
  rememberPosition
/>
```

### Props
    | Prop | Type | Default | Description |
| ------| ------| ---------| -------------|
| options | (string | { value: string; label: ReactNode; tag?: string })[] | ["One", "Two", "Three"] | The rows.A string is both value and label; a tag shows muted at the right. |
| value | string | undefined | Controlled value.Outside changes never animate. |
| defaultValue | string | undefined | Initial value when uncontrolled. |
| onChange | (value: string, option) => void | - | Called on a pick that changes the value. |
| placeholder | string | "Select…" | Chip text while nothing is selected. |
| showTags | boolean | true | Shows each row's tag. |
    | accentColor | string | "#f5f5f5" | The check on the selected row. |
| surfaceColor | string | "#27272a" | Chip and menu background. |
| highlightColor | string | "#3f3f46" | The gliding pill.The selected row rests on it at 60 %, and the chip tint derives from it. |
| textColor | string | "#f5f5f5" | Labels.Tags and the chevron derive from it. |
| size | "sm" | "md" | "lg" | "md" | Chip 28, 32 or 44 pixels with matching rows.Large is the touch - first size. |
| radius | number | 10 | Menu corner in pixels.Chip, rows and pill use 4 less so they stay concentric. |
| menuWidth | number | 176 | Menu width in pixels, never narrower than the chip. |
| placement | "top" | "bottom" | "bottom" | Which side the menu grows on.It flips when the chosen side would leave the viewport. |
| align | "left" | "right" | "left" | Which chip edge the menu shares. |
| popDuration | number | 180 | Milliseconds the menu takes to grow out of its corner.It leaves in two thirds of that. |
| glideDuration | number | 220 | Milliseconds the pill takes to travel between rows. 0 is a conventional hover. |
| rememberPosition | boolean | true | The highlight stays on the row the pointer left, so re - entry glides from there.Off, it clears on leave and the selected row shows again. |
| disabled | boolean | false | Dims the chip and ignores input. |
| ariaLabel | string | "Select" | Accessible name of the chip and list. |
| className | string | "" | Extra classes for the root. |

### Full Component Source
    ```jsx
import { useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import { HugeiconsIcon } from '@hugeicons/react';
import { ArrowDown01Icon, Tick02Icon } from '@hugeicons/core-free-icons';

import './GlideSelect.css';

const SIZES = {
  sm: { chip: 28, row: 26, font: 12 },
  md: { chip: 32, row: 30, font: 13 },
  lg: { chip: 44, row: 40, font: 14 }
};
const PAD = 4;
const GAP = 1;
const MENU_GAP = 6;
const DEFAULT_OPTIONS = ['One', 'Two', 'Three'];

const norm = o => (typeof o === 'string' ? { value: o, label: o } : o);
const textOf = it => (typeof it.label === 'string' ? it.label : it.value);
const typeaheadIndex = (items, from, ch) => {
  const c = ch.toLowerCase();
  const n = items.length;
  for (let k = 1; k <= n; k++) {
    const i = (from + k) % n;
    if (textOf(items[i]).toLowerCase().startsWith(c)) return i;
  }
  return from;
};

export default function GlideSelect({
  options = DEFAULT_OPTIONS,
  value,
  defaultValue,
  onChange,
  placeholder = 'Select…',
  showTags = true,
  accentColor = '#f5f5f5',
  surfaceColor = '#27272a',
  highlightColor = '#3f3f46',
  textColor = '#f5f5f5',
  size = 'md',
  radius = 10,
  menuWidth = 176,
  placement = 'bottom',
  align = 'left',
  popDuration = 180,
  glideDuration = 220,
  rememberPosition = true,
  disabled = false,
  ariaLabel = 'Select',
  className = ''
}) {
  const items = options.map(norm);
  const [inner, setInner] = useState(defaultValue ?? '');
  const current = value ?? inner;
  const selected = items.findIndex(it => it.value === current);
  const [phase, setPhase] = useState('closed');
  const [active, setActive] = useState(null);
  const [side, setSide] = useState(placement);
  const rootRef = useRef(null);
  const triggerRef = useRef(null);
  const menuRef = useRef(null);
  const pillRef = useRef(null);
  const instant = useRef(false);
  const closeTimer = useRef(undefined);
  const scrub = useRef(null);
  const id = useId();
  const S = SIZES[size] ?? SIZES.md;
  const step = S.row + GAP;
  const popOut = Math.round((popDuration * 2) / 3);

  useLayoutEffect(() => {
    if (phase !== 'open') return;
    const el = menuRef.current;
    const root = rootRef.current;
    if (!el || !root) return;
    const r = root.getBoundingClientRect();
    const need = el.offsetHeight + MENU_GAP;
    setSide(
      placement === 'bottom' && r.bottom + need > window.innerHeight
        ? 'top'
        : placement === 'top' && r.top - need < 0
          ? 'bottom'
          : placement
    );
    el.style.transitionDuration = instant.current ? '0ms' : '';
    el.dataset.state = 'closed';
    void el.offsetHeight;
    el.dataset.state = 'open';
    const p = pillRef.current;
    if (p) {
      p.style.transition = 'none';
      p.style.transform = `translateY(${ Math.max(0, selected) * step }px)`;
      p.style.opacity = '0';
      void p.offsetHeight;
      p.style.transition = '';
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase]);

  useLayoutEffect(() => {
    const p = pillRef.current;
    if (!p || phase !== 'open') return;
    if (active === null) {
      p.style.opacity = '0';
      return;
    }
    const jump = instant.current || p.style.opacity !== '1';
    p.style.transitionDuration = jump ? '0ms, 150ms' : '';
    p.style.transform = `translateY(${ active * step}px)`;
    p.style.opacity = '1';
    instant.current = false;
  }, [active, phase, step]);

  const open = viaKey => {
    if (disabled) return;
    clearTimeout(closeTimer.current);
    instant.current = true;
    setActive(selected >= 0 ? selected : viaKey ? 0 : null);
    setPhase('open');
  };
  const close = mode => {
    setActive(null);
    clearTimeout(closeTimer.current);
    const el = menuRef.current;
    if (mode === 'instant' || !el) {
      setPhase('closed');
      return;
    }
    el.style.transitionDuration = '';
    el.dataset.state = 'closed';
    setPhase('closing');
    closeTimer.current = setTimeout(() => setPhase('closed'), popOut + 20);
  };
  const pick = (i, viaKey) => {
    const it = items[i];
    if (!it) {
      close('instant');
      return;
    }
    if (it.value !== current) {
      if (value === undefined) setInner(it.value);
      onChange?.(it.value, it);
      if (!viaKey && rootRef.current) rootRef.current.dataset.swap = '';
    }
    close('instant');
    triggerRef.current?.focus({ preventScroll: true });
  };

  const onTriggerKey = e => {
    const k = e.key;
    const n = items.length;
    const cur = active ?? Math.max(0, selected);
    if (phase !== 'open') {
      if (k === 'Enter' || k === ' ' || k === 'ArrowDown' || k === 'ArrowUp') {
        e.preventDefault();
        open(true);
      }
      return;
    }
    const go = i => {
      e.preventDefault();
      instant.current = true;
      setActive(Math.min(n - 1, Math.max(0, i)));
    };
    if (k === 'ArrowDown' || k === 'ArrowUp') go(active === null ? cur : cur + (k === 'ArrowDown' ? 1 : -1));
    else if (k === 'Home' || k === 'End') go(k === 'Home' ? 0 : n - 1);
    else if (k === 'Enter' || k === ' ') {
      e.preventDefault();
      pick(cur, true);
    } else if (k === 'Escape' || k === 'Tab') {
      if (k === 'Escape') e.preventDefault();
      close('instant');
    } else if (k.length === 1 && !e.metaKey && !e.ctrlKey && !e.altKey) go(typeaheadIndex(items, cur, k));
  };

  useEffect(() => {
    if (phase === 'closed') return undefined;
    const onDown = e => {
      if (rootRef.current && !rootRef.current.contains(e.target)) close('pop');
    };
    document.addEventListener('pointerdown', onDown, true);
    return () => document.removeEventListener('pointerdown', onDown, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase]);
  useEffect(() => {
    if (disabled && phase !== 'closed') close('instant');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [disabled]);
  useEffect(() => () => clearTimeout(closeTimer.current), []);

  const rowAt = y => {
    const s = scrub.current;
    if (!s) return null;
    const i = Math.floor((y - s.top - PAD) / step);
    return i >= 0 && i < items.length ? i : null;
  };
  const onListDown = e => {
    if (scrub.current) return;
    try {
      e.currentTarget.setPointerCapture(e.pointerId);
    } catch {}
    scrub.current = { id: e.pointerId, top: e.currentTarget.getBoundingClientRect().top };
    instant.current = true;
    setActive(rowAt(e.clientY));
  };
  const onListMove = e => {
    if (!scrub.current || scrub.current.id !== e.pointerId) return;
    const i = rowAt(e.clientY);
    if (i !== active) setActive(i);
  };
  const onListUp = e => {
    if (!scrub.current || scrub.current.id !== e.pointerId) return;
    const i = e.type === 'pointerup' ? rowAt(e.clientY) : null;
    scrub.current = null;
    if (i !== null) pick(i, false);
    else if (!rememberPosition) setActive(null);
  };
  const onListOver = e => {
    if (e.pointerType === 'touch' || scrub.current) return;
    const row = e.target.closest('[data-index]');
    if (!row) return;
    const i = Number(row.dataset.index);
    if (i !== active) setActive(i);
  };

  const origin = `${ side === 'bottom' ? 'top' : 'bottom' } ${ align } `;
  return (
    <div
      ref={rootRef}
      className={`glide - select${ className ? ` ${className}` : '' } `}
      data-size={size}
      data-disabled={disabled ? '' : undefined}
      style={{
        '--gs-accent': accentColor,
        '--gs-surface': surfaceColor,
        '--gs-highlight': highlightColor,
        '--gs-text': textColor,
        '--gs-radius': `${ radius } px`,
        '--gs-inner-radius': `${ Math.max(3, radius - 4) } px`,
        '--gs-chip': `${ S.chip } px`,
        '--gs-row': `${ S.row } px`,
        '--gs-font': `${ S.font } px`,
        '--gs-menu-w': `${ menuWidth } px`,
        '--gs-pop': `${ popDuration } ms`,
        '--gs-pop-out': `${ popOut } ms`,
        '--gs-glide': `${ glideDuration } ms`,
        '--gs-origin': origin
      }}
      onAnimationEnd={e => {
        if (e.animationName === 'gs-swap' && rootRef.current) delete rootRef.current.dataset.swap;
      }}
    >
      <button
        ref={triggerRef}
        type="button"
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={phase === 'open'}
        aria-controls={`${ id } -list`}
        aria-activedescendant={active !== null ? `${ id } -${ active } ` : undefined}
        aria-label={ariaLabel}
        disabled={disabled}
        className="glide-select__trigger"
        onPointerDown={e => {
          if (e.button !== 0 || disabled) return;
          e.currentTarget.focus({ preventScroll: true });
          if (phase === 'open') close('pop');
          else open(false);
        }}
        onKeyDown={onTriggerKey}
      >
        <span className="glide-select__label" key={current} data-empty={selected < 0 ? '' : undefined}>
          {selected >= 0 ? items[selected].label : placeholder}
        </span>
        <span className="glide-select__chevron" aria-hidden="true">
          <HugeiconsIcon icon={ArrowDown01Icon} size={12} strokeWidth={2.5} />
        </span>
      </button>
      {phase !== 'closed' ? (
        <div ref={menuRef} className="glide-select__menu" data-state="open" data-side={side} data-align={align}>
          <div
            id={`${ id } -list`}
            role="listbox"
            aria-label={ariaLabel}
            className="glide-select__list"
            data-live={active !== null ? '' : undefined}
            onPointerOver={onListOver}
            onPointerLeave={() => {
              if (!scrub.current && !rememberPosition) setActive(null);
            }}
            onPointerDown={onListDown}
            onPointerMove={onListMove}
            onPointerUp={onListUp}
            onPointerCancel={onListUp}
            onLostPointerCapture={onListUp}
          >
            <span ref={pillRef} className="glide-select__pill" aria-hidden="true" />
            {items.map((it, i) => (
              <div
                key={it.value}
                id={`${ id } -${ i } `}
                role="option"
                aria-selected={i === selected}
                data-index={i}
                className="glide-select__option"
              >
                <span className="glide-select__name">{it.label}</span>
                {showTags && it.tag ? <span className="glide-select__tag">{it.tag}</span> : null}
                <span className="glide-select__check" data-on={i === selected ? '' : undefined} aria-hidden="true">
                  <HugeiconsIcon icon={Tick02Icon} size={13} strokeWidth={2.5} />
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

```

### Component CSS
    ```css
.glide-select {
  --gs-accent: #f5f5f5;
  --gs-surface: #27272a;
  --gs-highlight: #3f3f46;
  --gs-text: #f5f5f5;
  --gs-radius: 10px;
  --gs-inner-radius: 6px;
  --gs-chip: 32px;
  --gs-row: 30px;
  --gs-font: 13px;
  --gs-menu-w: 176px;
  --gs-pop: 180ms;
  --gs-pop-out: 120ms;
  --gs-glide: 220ms;
  --gs-origin: top left;
  --gs-ease-out: cubic-bezier(0.23, 1, 0.32, 1);

  position: relative;
  display: inline-block;
}

.glide-select[data-disabled] {
  opacity: 0.5;
}

.glide-select__trigger {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: var(--gs-chip);
  margin: 0;
  padding: 0 8px 0 10px;
  border: 0;
  border-radius: var(--gs-inner-radius);
  background: var(--gs-surface);
  color: var(--gs-text);
  font-family: inherit;
  font-size: var(--gs-font);
  font-weight: 500;
  line-height: 1;
  cursor: pointer;
  outline: none;
  user-select: none;
  -webkit-user-select: none;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
  transition:
    background-color 100ms ease,
    transform 160ms var(--gs-ease-out);
}

.glide-select__trigger:disabled {
  cursor: default;
}

@media (hover: hover) and (pointer: fine) {
  .glide-select__trigger:not(:disabled):hover {
    background: color-mix(in srgb, var(--gs-highlight) 60%, var(--gs-surface));
  }
}

.glide-select__trigger[aria-expanded='true'] {
  background: color-mix(in srgb, var(--gs-highlight) 60%, var(--gs-surface));
}

.glide-select__trigger:not(:disabled):active {
  transform: scale(0.97);
}

.glide-select__label[data-empty] {
  opacity: 0.6;
}

.glide-select[data-swap] .glide-select__label {
  animation: gs-swap 160ms ease;
}

@keyframes gs-swap {
  from {
    opacity: 0.6;
    filter: blur(2px);
  }
}

.glide-select__chevron {
  display: inline-flex;
  color: color-mix(in srgb, var(--gs-text) 55%, transparent);
  transition: transform 200ms var(--gs-ease-out);
}

.glide-select__trigger[aria-expanded='true'] .glide-select__chevron {
  transform: rotate(180deg);
}

.glide-select__menu {
  position: absolute;
  z-index: 20;
  width: var(--gs-menu-w);
  min-width: 100%;
  padding: 4px;
  border-radius: var(--gs-radius);
  background: var(--gs-surface);
  box-shadow: 0 4px 16px color-mix(in srgb, #000 22%, transparent);
  transform-origin: var(--gs-origin);
  opacity: 0;
  transform: scale(0.95);
  transition:
    opacity var(--gs-pop) var(--gs-ease-out),
    transform var(--gs-pop) var(--gs-ease-out);
}

.glide-select__menu[data-state='open'] {
  opacity: 1;
  transform: none;
}

.glide-select__menu[data-state='closed'] {
  transition-duration: var(--gs-pop-out);
  pointer-events: none;
}

.glide-select__menu[data-side='bottom'] {
  top: calc(100% + 6px);
}

.glide-select__menu[data-side='top'] {
  bottom: calc(100% + 6px);
}

.glide-select__menu[data-align='left'] {
  left: 0;
}

.glide-select__menu[data-align='right'] {
  right: 0;
}

.glide-select__list {
  position: relative;
  display: grid;
  gap: 1px;
  touch-action: none;
}

.glide-select__pill {
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  height: var(--gs-row);
  border-radius: var(--gs-inner-radius);
  background: var(--gs-highlight);
  opacity: 0;
  pointer-events: none;
  transition:
    transform var(--gs-glide) var(--gs-ease-out),
    opacity 150ms ease;
}

.glide-select__option {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  height: var(--gs-row);
  padding: 0 8px 0 10px;
  border-radius: var(--gs-inner-radius);
  color: var(--gs-text);
  font-size: var(--gs-font);
  cursor: pointer;
  user-select: none;
  -webkit-user-select: none;
  -webkit-tap-highlight-color: transparent;
  transition: background-color 150ms ease;
}

.glide-select__option[aria-selected='true'] {
  background: color-mix(in srgb, var(--gs-highlight) 60%, transparent);
}

.glide-select__list[data-live] .glide-select__option[aria-selected='true'] {
  background: transparent;
}

.glide-select__name {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  font-weight: 500;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.glide-select__tag {
  flex-shrink: 0;
  color: color-mix(in srgb, var(--gs-text) 55%, transparent);
  font-size: calc(var(--gs-font) - 2px);
}

.glide-select__check {
  display: inline-flex;
  flex-shrink: 0;
  color: var(--gs-accent);
  visibility: hidden;
}

.glide-select__check[data-on] {
  visibility: visible;
}

@media (prefers-reduced-motion: reduce) {
  .glide-select__menu {
    transform: none !important;
    transition: opacity var(--gs-pop) ease;
  }

  .glide-select__menu[data-state='closed'] {
    transition-duration: var(--gs-pop-out);
  }

  .glide-select__pill {
    transition: opacity 150ms ease;
  }

  .glide-select__chevron {
    transition: none;
  }

  .glide-select__trigger {
    transition: background-color 100ms ease;
  }

  .glide-select__trigger:not(:disabled):active {
    transform: none;
  }

  .glide-select[data-swap] .glide-select__label {
    animation: none;
  }
}

```

### Integration Instructions
1. Install any listed dependencies.
2. Copy the component source into the appropriate directory in the project.
3. Import the CSS file alongside the component.
4. Import and render the component using the usage example above as a starting point.
5. Adjust props as needed for the specific use case — refer to the props table for all available options.

### More from React Bits
The full library index, including everything reactbits.dev offers, is at https://reactbits.dev/llms.txt — fetch it if this component is not the right fit or the project needs more pieces.
