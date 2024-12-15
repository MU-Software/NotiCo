import { RJSFSchema } from "@rjsf/utils"

export type APIErrorResponseType = {
  traceback: string
}

export type ServiceDefType = {
  name: string
  template_schema: RJSFSchema
}

export type TemplateMangerServiceListResponse = {
  name: string
  template_schema: Record<string, unknown>
}[]

export type TemplateDefType = {
  template_code: string
  template: Record<string, unknown>
  template_variables: string[]
}

export type TemplateManagerSimpleRequest = {
  service_name: string
}
export type TemplateManagerDetailRequest = {
  service_name: string
  template_code: string
}
export type TemplateManagerModifyRequest = {
  service_name: string
  template_code: string
  template: Record<string, unknown>
}

export type TemplateManagerRenderRequest = {
  service_name: string
  template_code: string
} & Record<string, unknown>
export type TemplateManagerRenderJSONResponse = {
  render_result: Record<string, unknown>
}
export type TemplateManagerRenderHTMLResponse = string

export type SendRequestType = {
  service_name: string
  template_code: string
  shared_context: Record<string, unknown>
  personalized_context: {[k in string]: Record<string, unknown>}
}
