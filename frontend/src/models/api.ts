import { RJSFSchema } from "@rjsf/utils"

export type APIErrorResponseType = {
  traceback: string
}

export type ServiceDefType = {
  name: string
  permission: TemplateManagerPermissionType
  template_schema: RJSFSchema
}

export type TemplateManagerPermissionType = {
  list: boolean
  retrieve: boolean
  create: boolean
  update: boolean
  delete: boolean
}
export type TemplateMangerServiceListResponse = ServiceDefType[]

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

export type SendManagerListResponse = {
  name: string
  template_schema: RJSFSchema
}
export type SendRequestType = {
  service_name: string
  template_code: string
  shared_context: Record<string, unknown>
  personalized_context: {[k in string]: Record<string, unknown>}
}
