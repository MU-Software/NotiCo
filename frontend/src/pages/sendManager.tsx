import React from 'react'

import { Box, Button, CircularProgress, FormControl, InputLabel, MenuItem, Select, Stack, Tooltip, Typography } from '@mui/material'
import { IChangeEvent } from '@rjsf/core'
import Form from '@rjsf/mui'
import { RJSFSchema, StrictRJSFSchema } from '@rjsf/utils'
import validator from '@rjsf/validator-ajv8'
import { wrap } from '@suspensive/react'
import { OptionsObject, VariantType, enqueueSnackbar } from 'notistack'
import * as R from 'remeda'

import { useListTemplatesQuery, useRenderTemplateHtmlMutation, useSendManagerServicesQuery, useSendNotificationMutation } from '../hooks/useAPIs'
import { ServiceDefType, TemplateDefType } from '../models/api'
import { getErrorString } from '../utils/error'

const getDefaultSnackOption: (v: VariantType) => OptionsObject = (v) => ({ variant: v, anchorOrigin: { vertical: 'bottom', horizontal: 'center' } })

const convertTemplateVarToJsonSchema: (_: { vars: string[] }) => RJSFSchema = ({ vars }) => ({
  type: 'object',
  required: vars,
  properties: vars.reduce((acc, v) => {
    let propertyInfo: StrictRJSFSchema = { type: 'string' }
    if (v.includes('url')) propertyInfo = { type: 'string', pattern: '^[a-z0-9-]+(\\.[a-z0-9-]+)+([/?].*)?$' }
    else if (v.includes('email')) propertyInfo = { type: 'string', format: 'email' }
    else if (v.includes('phone')) propertyInfo = { type: 'string', pattern: '^\\d{2,3}-\\d{3,4}-\\d{4}$' }
    else if (v.includes('datetime')) propertyInfo = { type: 'string', format: 'date-time' }
    else if (v.includes('date')) propertyInfo = { type: 'string', format: 'date' }
    else if (v.includes('time')) propertyInfo = { type: 'string', format: 'time' }
    else if (v === 'send_to') propertyInfo = { type: 'string', title: '보낼 주소 또는 연락처' }

    return { ...acc, [v]: propertyInfo }
  }, {})
})

type FormDataType = { send_to: string } & Record<string, string>
type SendManagerTemplateStateType = {
  t?: TemplateDefType
  formData?: FormDataType
  isFormValidated?: boolean
  previewHTML?: string
}
type SendManagerFormDataEventType = IChangeEvent<FormDataType, RJSFSchema, { [k in string]: unknown }>

const SendManagerTemplateContainer: React.FC<{ service: ServiceDefType; templates: { [k in string]: TemplateDefType } }> = ({ service, templates }) => {
  const previewRef = React.useRef<HTMLDivElement>(null)
  const renderPreviewHTMLMutation = useRenderTemplateHtmlMutation()
  const sendNotificationMutation = useSendNotificationMutation()
  const [state, setState] = React.useState<SendManagerTemplateStateType>({})
  const addSnackbar = (c: string | React.ReactNode, v: VariantType) => enqueueSnackbar(c, getDefaultSnackOption(v))

  React.useEffect(() => setState(({})), [service])
  React.useEffect(() => { if (previewRef.current) previewRef.current.innerHTML = state.previewHTML ?? '' }, [state.previewHTML])

  const resetForm: () => void = () => setState(ps => ({ ...ps, isFormValidated: false, formData: undefined, previewHTML: undefined }))
  const change: (data: SendManagerFormDataEventType, id?: string) => void = ({ formData }) => setState(ps => ({ ...ps, formData, isFormValidated: false }))
  const render: (data: SendManagerFormDataEventType, event: React.FormEvent<unknown>) => void = ({ formData }) => renderPreviewHTMLMutation.mutate(
    { service_name: service.name, template_code: state.t?.template_code ?? '', ...formData },
    {
      onSuccess: (data) => {
        setState(ps => ({ ...ps, previewHTML: data, isFormValidated: true }))
        addSnackbar('미리보기 준비 완료!', 'success')
      },
      onError: (error) => addSnackbar(
        <Stack>
          미리보기 준비 중 문제가 발생했습니다.<br />
          <pre style={{ whiteSpace: 'pre-wrap' }}>{getErrorString(error)}</pre>
        </Stack>,
        'error',
      ),
    }
  )
  const send: () => void = () => sendNotificationMutation.mutate(
    {
      service_name: service.name,
      template_code: state.t?.template_code ?? '',
      shared_context: {},
      personalized_context: { [state.formData?.send_to ?? '']: state.formData ?? {} }
    },
    {
      onSuccess: () => addSnackbar('알림 전송 성공!', 'success'),
      onError: (error) => addSnackbar(
        <Stack>
          알림 전송 중 문제가 발생했습니다.<br />
          <pre style={{ whiteSpace: 'pre-wrap' }}>{getErrorString(error)}</pre>
        </Stack>,
        'error',
      ),
    }
  )

  const sortedTemplateVariables = state.t?.template_variables.sort() ?? []
  const isPending = renderPreviewHTMLMutation.isPending || sendNotificationMutation.isPending
  const isSendable = state.isFormValidated && !isPending

  return R.isEmpty(Object.entries(templates))
    ? <Typography>템플릿이 없습니다.</Typography>
    : <Stack>
      <FormControl>
        <InputLabel id='s-t-label'>템플릿</InputLabel>
        <Select labelId='s-t-label' id='s-t' label='템플릿' onChange={(e) => setState(({ t: templates[e.target.value as string] }))} value={state.t?.template_code ?? ''}>
          {Object.keys(templates).map((n) => <MenuItem key={n} value={n}>{n}</MenuItem>)}
        </Select>
      </FormControl>
      <br />
      {
        state.t && <Stack direction={{ xs: 'column-reverse', sm: 'row' }} spacing={2}>
          <Box sx={{ width: '100%' }}>
            <Typography variant='h5'><b>템플릿 변수 설정</b></Typography>
            <Form
              schema={convertTemplateVarToJsonSchema({ vars: ['send_to', ...sortedTemplateVariables] })}
              uiSchema={{ 'ui:title': '', 'ui:order': ['send_to', ...sortedTemplateVariables] }}
              validator={validator}
              formData={state.formData}
              liveValidate
              focusOnFirstError
              showErrorList='bottom'
              onSubmit={render}
              onChange={change}
              disabled={isPending}
            >
              <Stack direction="row" spacing={2} sx={{ justifyContent: 'space-between', margin: '0 0 0.5rem 0' }}>
                <Stack direction="row" spacing={2}>
                  <Button disabled={isPending} variant="contained" type="submit">미리보기</Button>
                  <Button disabled={isPending} color="error" onClick={resetForm}>초기화</Button>
                </Stack>
                {
                  state.isFormValidated
                    ? <Button variant="contained" color="success" disabled={!isSendable} onClick={send}>보내기</Button>
                    : <Tooltip title='먼저 미리보기로 리뷰를 진행해주세요.'><Box><Button variant="contained" disabled>보내기</Button></Box></Tooltip>
                }
              </Stack>
            </Form>
          </Box>
          <Box sx={{ width: '100%' }}>
            <Typography variant='h5'><b>미리보기</b></Typography>
            <Stack sx={{ width: '100%', height: '100%' }}>
              <div style={{ width: '100%', height: '100%', display: 'flex', justifyContent: 'center' }} ref={previewRef}></div>
            </Stack>
          </Box>
        </Stack>
      }
    </Stack>
}

const SendManagerServiceContainer: React.FC<{ services: { [k in string]: ServiceDefType } }> = ({ services }) => {
  const [state, setState] = React.useState<{ s?: ServiceDefType }>({})

  const SendManagerTemplateWrapper = wrap
    .ErrorBoundary({ fallback: <Box sx={{ color: 'red' }}>템플릿 목록을 가져오는 중 문제가 발생했습니다,<br />새로고침 해주세요.</Box> })
    .Suspense({ fallback: <CircularProgress /> })
    .on(({ service }: { service: ServiceDefType }) => {
      // eslint-disable-next-line react-hooks/rules-of-hooks
      const { data } = useListTemplatesQuery(service.name)
      return <SendManagerTemplateContainer service={service} templates={data.reduce((acc, t) => ({ ...acc, [t.template_code]: t }), {})} />
    })

  return services ? <Stack>
    <FormControl>
      <InputLabel id='s-s-label'>서비스</InputLabel>
      <Select labelId='s-s-label' id='s-s' label='서비스' onChange={(e) => setState({ s: services[e.target.value as string] })} value={state.s?.name ?? ''}>
        {Object.keys(services).map((n) => <MenuItem key={n} value={n}>{n}</MenuItem>)}
      </Select>
    </FormControl>
    <br />
    {state.s && <SendManagerTemplateWrapper service={state.s} />}
  </Stack> : <></>
}

export const SendManagerPage: React.FC = wrap
  .ErrorBoundary({ fallback: <Box sx={{ color: 'red' }}>서비스 목록을 가져오는 중 문제가 발생했습니다,<br />새로고침 해주세요.</Box> })
  .Suspense({ fallback: <CircularProgress /> })
  .on(() => {
    const { data } = useSendManagerServicesQuery()
    return <SendManagerServiceContainer services={data.reduce((acc, s) => ({ ...acc, [s.name]: s }), {})} />
  })
