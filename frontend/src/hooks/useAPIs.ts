import { useMutation, useSuspenseQuery } from '@tanstack/react-query'
import * as R from 'remeda'

import { MSDomain } from '../consts/application'
import {
  APIErrorResponseType,
  SendManagerListResponse,
  SendRequestType,
  TemplateDefType,
  TemplateManagerDetailRequest,
  TemplateManagerModifyRequest,
  TemplateManagerRenderHTMLResponse,
  TemplateManagerRenderJSONResponse,
  TemplateManagerRenderRequest,
  TemplateMangerServiceListResponse
} from '../models/api'

const DEFAULT_TIMEOUT = 15 * 1000 // 15 seconds

export type RequestFetchMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

export type RequestFetchArguments = {
  route: string
  method: RequestFetchMethod
  headers?: Record<string, string>
  data?: Record<string, unknown> | Record<string, unknown>[]
  expectedMediaType?: string
}

const isJsonParsable = (data: unknown): boolean => {
  try {
    JSON.parse(data as string)
    return true
  } catch (e: unknown) {
    console.log('isJsonParsable', e)
    return false
  }
}

const isAPIErrorResponseType = (data: unknown): data is APIErrorResponseType => {
  const errObjChecker = R.allPass<APIErrorResponseType>([R.isObjectType, (d) => R.isString(d.traceback)])

  try {
    return errObjChecker(data as APIErrorResponseType)
  } catch (e: unknown) {
    console.log('isAPIErrorResponseType', e)
    return false
  }
}

export class RequestError extends Error {
  readonly status: number
  readonly payload: string

  constructor(message: string, status: number, payload: string) {
    super(message)
    this.name = 'RequestError'
    this.status = status
    this.payload = payload
  }

  toAlertString() {
    if (isJsonParsable(this.payload)) {
      const errObj = JSON.parse(this.payload)
      return ((isAPIErrorResponseType(errObj) && errObj.traceback) || errObj.message) ?? this.message
    }

    return this.message
  }
}

export const LocalRequest: <T>(reqOption: RequestFetchArguments) => Promise<T> = async (reqOption) => {
  const result = await fetch(`${MSDomain}/${reqOption.route}`, {
    method: reqOption.method,
    cache: 'no-cache',
    redirect: 'follow',
    signal: AbortSignal.timeout(DEFAULT_TIMEOUT),
    headers: new Headers({ 'Content-Type': 'application/json', ...reqOption.headers }),
    credentials: 'include',
    referrerPolicy: 'origin',
    mode: 'cors',
    ...(['POST', 'PUT', 'PATCH'].includes(reqOption.method) ? { body: JSON.stringify(reqOption.data ?? {}) as BodyInit } : {}),
  })
  if (!result.ok) throw new RequestError('요청에 실패했습니다.', result.status, await result.text())

  return reqOption.expectedMediaType === undefined || reqOption.expectedMediaType === 'application/json' ? await result.json() : await result.text()
}

export const QUERY_KEYS = {
  LIST_TEMPLATE_MANAGER_SERVICE: ['query', 'list', 'template-manager', 'service'] as const,
  LIST_TEMPLATE: ['query', 'template', 'list'] as const,
  LIST_SEND_MANAGER_SERVICE: ['query', 'list', 'send-manager', 'service'] as const,
}

export const MUTATION_KEYS = {
  CREATE_TEMPLATE: ['mutation', 'template', 'create'] as const,
  RETRIEVE_TEMPLATE: ['mutation', 'template', 'retrieve'] as const,
  UPDATE_TEMPLATE: ['mutation', 'template', 'update'] as const,
  DELETE_TEMPLATE: ['mutation', 'template', 'delete'] as const,
  RENDER_TEMPLATE_JSON: ['mutation', 'render', 'send', 'json'] as const,
  RENDER_TEMPLATE_HTML: ['mutation', 'render', 'send', 'html'] as const,
  SEND_NOTIFICATION: ['mutation', 'send', 'notification'] as const,
}

// ==================== Query Hooks ====================
export const useListTemplateManagerServicesQuery = () =>
  useSuspenseQuery({
    queryKey: QUERY_KEYS.LIST_TEMPLATE_MANAGER_SERVICE,
    queryFn: () => LocalRequest<TemplateMangerServiceListResponse>({ route: 'api/v1/template-manager', method: 'GET' }),
  })

export const useListTemplatesQuery = (serviceName: string) =>
  useSuspenseQuery({
    queryKey: [...QUERY_KEYS.LIST_TEMPLATE, serviceName],
    queryFn: () => LocalRequest<TemplateDefType[]>({ route: `api/v1/template-manager/${serviceName}`, method: 'GET' }),
  })

export const useSendManagerServicesQuery = () =>
  useSuspenseQuery({
    queryKey: QUERY_KEYS.LIST_SEND_MANAGER_SERVICE,
    queryFn: () => LocalRequest<SendManagerListResponse[]>({ route: 'api/v1/send-manager', method: 'GET' }),
  })
// ==================== Mutation Hooks ====================
export const useCreateTemplateMutation = () =>
  useMutation({
    mutationKey: MUTATION_KEYS.CREATE_TEMPLATE,
    mutationFn: (data: TemplateManagerModifyRequest) => LocalRequest<TemplateDefType>({ route: `api/v1/template-manager/${data.service_name}/${data.template_code}`, method: 'POST', data }),
  })

export const useRetrieveTemplateMutation = () =>
  useMutation({
    mutationKey: MUTATION_KEYS.RETRIEVE_TEMPLATE,
    mutationFn: (data: TemplateManagerDetailRequest) => LocalRequest<TemplateDefType>({ route: `api/v1/template-manager/${data.service_name}/${data.template_code}`, method: 'GET' }),
  })

export const useUpdateTemplateMutation = () =>
  useMutation({
    mutationKey: MUTATION_KEYS.UPDATE_TEMPLATE,
    mutationFn: (data: TemplateManagerModifyRequest) => LocalRequest<TemplateDefType>({ route: `api/v1/template-manager/${data.service_name}/${data.template_code}`, method: 'PUT', data }),
  })

export const useDeleteTemplateMutation = () =>
  useMutation({
    mutationKey: MUTATION_KEYS.UPDATE_TEMPLATE,
    mutationFn: (data: TemplateManagerDetailRequest) => LocalRequest<void>({ route: `api/v1/template-manager/${data.service_name}/${data.template_code}`, method: 'DELETE' }),
  })

export const useRenderTemplateJsonMutation = () =>
  useMutation({
    mutationKey: MUTATION_KEYS.RENDER_TEMPLATE_JSON,
    mutationFn: (data: TemplateManagerRenderRequest) => LocalRequest<TemplateManagerRenderJSONResponse>({
      route: `api/v1/template-manager/${data.service_name}/${data.template_code}/render`,
      method: 'POST',
      headers: { Accept: 'application/json' },
      data,
    }),
  })

export const useRenderTemplateHtmlMutation = () =>
  useMutation({
    mutationKey: MUTATION_KEYS.RENDER_TEMPLATE_HTML,
    mutationFn: (data: TemplateManagerRenderRequest) => LocalRequest<TemplateManagerRenderHTMLResponse>({
      route: `api/v1/template-manager/${data.service_name}/${data.template_code}/render`,
      method: 'POST',
      headers: { Accept: 'text/html' },
      expectedMediaType: 'text/html',
      data,
    }),
  })

export const useSendNotificationMutation = () =>
  useMutation({
    mutationKey: MUTATION_KEYS.SEND_NOTIFICATION,
    mutationFn: (data: SendRequestType) => LocalRequest<Record<string, unknown>>({ route: `api/v1/send-manager/${data.service_name}`, method: 'POST', data }),
  })
