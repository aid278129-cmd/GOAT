# Morphing infinity (/docs/components/morphing-infinity)



`MorphingInfinity` is an animated line icon that cycles through circle and
infinity forms. It is a good fit for AI replies, drafting flows, planning states,
and any interface where the wait state should feel deliberate instead of
generic.

<ComponentPreview name="morphing-infinity-demo" />

## Installation [#installation]

<CodeTabs>
  <TabsList>
    <TabsTrigger value="cli">
      Command
    </TabsTrigger>

    <TabsTrigger value="manual">
      Manual
    </TabsTrigger>
  </TabsList>

  <TabsContent value="cli">
    ```bash
    npx shadcn@latest add @loading-ui/morphing-infinity
    ```
  </TabsContent>

  <TabsContent value="manual">
    <Steps className="mb-0 pt-2">
      <Step>
        Copy and paste the following code into your project.
      </Step>

      <ComponentSource name="morphing-infinity" title="components/loading-ui/morphing-infinity.tsx" />

      <Step>
        Update the import paths to match your project setup.
      </Step>
    </Steps>
  </TabsContent>
</CodeTabs>

## Usage [#usage]

```tsx
import { MorphingInfinity } from "@/components/loading-ui/morphing-infinity";
```

```tsx
<MorphingInfinity />
```

## Customization [#customization]

`MorphingInfinity` is an SVG with a morphing path stroke. Use `className` and
`size-*` utilities to scale it inline, and inherit `currentColor` from the
surrounding text or foreground utilities.

### Compact [#compact]

Use a smaller `size-*` when the icon appears inside dense assistant panels,
toolbars, or inline status rows.

<ComponentPreview name="morphing-infinity-compact" />

## Examples [#examples]

These examples place the morphing infinity in assistant-oriented surfaces where
a compact loading indicator needs to remain visible without becoming a full-page
loader.

### Alert [#alert]

Alerts can pair the icon with one concise line about the work in progress.

<ComponentPreview name="morphing-infinity-alert" />

### Card [#card]

Cards keep the state attached to a specific assistant workspace or processing
panel.

<ComponentPreview name="morphing-infinity-card" />

### Tabs [#tabs]

Tabs work well when generated content and supporting material resolve at
different moments.

<ComponentPreview name="morphing-infinity-tabs" />
