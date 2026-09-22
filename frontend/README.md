# MERIDIAN Console

The operator interface for the MERIDIAN compliance engine. React, TypeScript
and Vite.

## Build

The production build is written directly into the engine package
(`meridian/api/static/dashboard`), so a deployment serves the console and the
application programming interface from one process and one origin.

```bash
npm install
npm run build
```

## Development

Start the engine first, then the development server. The development server
proxies `/api` to the engine, so the browser sees a single origin and no
cross-origin configuration is required.

```bash
npm run dev
```

The console is then served at `http://localhost:5173/dashboard`.

Note that the development server and the engine-served console are different
origins, and sessions are held per origin. A sign-in on one does not carry to
the other.

## Conventions

- **All seven result states must be carried through to the interface.**
  Collapsing them to pass and fail would misrepresent the assessment: an
  undecided control rendered as a pass is precisely the failure this product
  exists to detect. `UNKNOWN` and `NOT_APPLICABLE` are rendered in a neutral
  colour and never in the colour used for a pass.
- **Every request must carry credentials.** Requests are issued through the
  helpers in `src/lib/api.ts`, which attach the session token. A bare `fetch`,
  or a link pointing directly at an endpoint, will be rejected as
  unauthenticated.
- **The design system redefines several spacing utilities.** `--spacing-8`,
  `-16`, `-24`, `-32`, `-40`, `-48`, `-56`, `-64`, `-72` and `-96` are declared
  in `@theme`, so `p-8` resolves to 8 pixels rather than 32, and `w-56` to 56
  pixels rather than 224. Use a value absent from that list, or an explicit
  pixel value.

## Linting

```bash
npm run lint
```
