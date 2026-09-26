# Text shimmer (/docs/components/text-shimmer)



`TextShimmer` sweeps a highlight across a line of text. It feels more polished
than dots or blinking, so it is a good fit for generated summaries, AI copy,
document scanning, and premium-feeling loading labels.

<ComponentPreview name="text-shimmer-demo" />

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
    npx shadcn@latest add @loading-ui/text-shimmer
    ```
  </TabsContent>

  <TabsContent value="manual">
    <Steps className="mb-0 pt-2">
      <Step>
        Copy and paste the following code into your project.
      </Step>

      <ComponentSource name="text-shimmer" title="components/loading-ui/text-shimmer.tsx" />

      <Step>
        Update the import paths to match your project setup.
      </Step>
    </Steps>
  </TabsContent>
</CodeTabs>

## Usage [#usage]

```tsx
import { TextShimmer } from "@/components/loading-ui/text-shimmer";
```

```tsx
<TextShimmer>Thinking</TextShimmer>
```

## Customization [#customization]

`TextShimmer` uses a text-clipped gradient. Keep the copy short enough that the
sweep reads as progress instead of becoming a decorative headline.

### Color [#color]

By default, `TextShimmer` derives both colors from `currentColor`, so it follows
filled buttons, badges, and muted text automatically. Use `baseColor` and
`shimmerColor` directly when you need explicit swatches.

<ComponentPreview name="text-shimmer-color" />

### Duration [#duration]

Longer copy usually benefits from a slightly slower sweep.

<ComponentPreview name="text-shimmer-duration" />

### Spread [#spread]

`spread` controls how wide the bright part of the sweep becomes.

<ComponentPreview name="text-shimmer-spread" />

## Examples [#examples]

These examples use shimmer where the text itself is the loading surface:
generated labels, assistant copy, and scan states.

### Button [#button]

Inside filled buttons, the shimmer follows the button foreground automatically.

<ComponentPreview name="text-shimmer-button" />

### Badge [#badge]

Shimmer badges are useful for generated or indexing states without adding a
separate icon.

<ComponentPreview name="text-shimmer-badge" />

### Input Group [#input-group]

Input addons can show that a prompt, query, or answer is being assembled.

<ComponentPreview name="text-shimmer-input-group" />

### Alert [#alert]

Use alerts when the shimmer headline needs supporting context.

<ComponentPreview name="text-shimmer-alert" />
