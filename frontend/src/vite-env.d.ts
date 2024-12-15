/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_MICROSERVICE_NAME: string
  readonly VITE_MICROSERVICE_DOMAIN: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
