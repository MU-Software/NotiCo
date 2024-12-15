import React from 'react'

import { Box, Button, CircularProgress, FormControl, InputLabel, MenuItem, Select, Stack, Tab, Tabs, TextField, Tooltip, Typography } from '@mui/material'
import { IChangeEvent } from '@rjsf/core'
import Form from '@rjsf/mui'
import { RJSFSchema, UiSchema, WidgetProps } from '@rjsf/utils'
import validator from '@rjsf/validator-ajv8'
import { wrap } from '@suspensive/react'
import * as R from 'remeda'

import { useQueryClient } from '@tanstack/react-query'
import { OptionsObject, VariantType, enqueueSnackbar } from 'notistack'
import { QUERY_KEYS, useCreateTemplateMutation, useDeleteTemplateMutation, useListTemplateManagerServicesQuery, useListTemplatesQuery, useRenderTemplateHtmlMutation, useUpdateTemplateMutation } from '../hooks/useAPIs'
import { ServiceDefType, TemplateDefType } from '../models/api'
import { getErrorString } from '../utils/error'

type TemplateType = Record<string, unknown>
type TemplateManagerFormDataEventType = IChangeEvent<TemplateType, RJSFSchema, { [k in string]: unknown }>
type TemplateEditorStateType = {
  formData?: TemplateType
  isFormSaved?: boolean
  previewHTML?: string
}

const TabPanel: React.FC<React.PropsWithChildren<{ value: number; index: number }>> = ({ children, value, index }) => (
  <div hidden={value !== index}>{value === index && <Box sx={{ p: 3 }}>{children}</Box>}</div>
)

const getDefaultSnackOption: (v: VariantType) => OptionsObject = (v) => ({ variant: v, anchorOrigin: { vertical: 'bottom', horizontal: 'center' } })

const convertTemplateVarToUISchema: (_: { vars: string[] }) => UiSchema = ({ vars }) => vars.reduce((acc, v) => {
  let uiSchemaInfo: UiSchema = {}
  if (['body', 'templateContent'].includes(v)) uiSchemaInfo = {
    'ui:widget': (props: WidgetProps) => <TextField
      className={props.className}
      id={`${props.id} ${props.disabled ? 'outlined-textarea-static' : 'outlined-textarea'}`}
      value={props.value}
      required={props.required}
      disabled={props.disabled}
      autoFocus={props.autofocus}
      placeholder={props.placeholder}
      label={props.label}
      onChange={(e) => props.onChange(e.target.value)}
      multiline
    />
  }

  return { ...acc, ...(uiSchemaInfo && { [v]: uiSchemaInfo }) }
}, { 'ui:title': '', 'ui:order': ['template_code', '*'] })

type TemplateEditorProps = {
  service: ServiceDefType
  template?: TemplateDefType
  disabled?: boolean
}
const TemplateEditor: React.FC<TemplateEditorProps> = ({ service, template, disabled }) => {
  const previewRef = React.useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()
  const createTemplateMutation = useCreateTemplateMutation()
  const updateTemplateMutation = useUpdateTemplateMutation()
  const renderPreviewHTMLMutation = useRenderTemplateHtmlMutation()
  const [state, setState] = React.useState<TemplateEditorStateType>({
    formData: template ? { ...template.template, template_code: template.template_code } : undefined,
    isFormSaved: template !== undefined
  })
  const addSnackbar = (c: string | React.ReactNode, v: VariantType) => enqueueSnackbar(c, getDefaultSnackOption(v))

  React.useEffect(() => setState(({})), [service])
  React.useEffect(() => setState(ps => ({
    ...ps,
    formData: template ? { ...template.template, template_code: template.template_code } : undefined,
    isFormSaved: template !== undefined,
  })), [template])
  React.useEffect(() => { if (previewRef.current) previewRef.current.innerHTML = state.previewHTML ?? '' }, [state.previewHTML])

  const change: (data: TemplateManagerFormDataEventType, id?: string) => void = ({ formData }) => {
    console.log('changed', formData)
    setState(ps => ({ ...ps, formData, isFormSaved: false }))
  }
  const submit: (data: TemplateManagerFormDataEventType, event: React.FormEvent<unknown>) => void = ({ formData }) => {
    console.log('submitted', formData)
    setState(ps => ({ ...ps, formData, isFormSaved: false }))

    if (!formData) return

    (template ? updateTemplateMutation : createTemplateMutation).mutate(
      { service_name: service.name, template_code: formData.template_code as string, template: formData },
      {
        onSuccess: () => {
          setState(ps => ({ ...ps, isFormSaved: true }))
          addSnackbar('템플릿 저장 완료!', 'success')
          queryClient.invalidateQueries({ queryKey: QUERY_KEYS.LIST_TEMPLATE })
        },
        onError: (error) => addSnackbar(
          <Stack>
            템플릿 저장 중 문제가 발생했습니다.<br />
            <pre style={{ whiteSpace: 'pre-wrap' }}>{getErrorString(error)}</pre>
          </Stack>,
          'error',
        ),
      }
    )
  }
  const preview: () => void = () => {
    if (!state.formData) return
    renderPreviewHTMLMutation.mutate(
      {
        service_name: service.name,
        template_code: state.formData.template_code as string,
        not_defined_variable_handling: 'show_as_template_var',
      },
      {
        onSuccess: (data) => {
          setState(ps => ({ ...ps, previewHTML: data }))
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
  }

  const isPending = disabled || createTemplateMutation.isPending || updateTemplateMutation.isPending || renderPreviewHTMLMutation.isPending
  const isPreviewAvailable = state.isFormSaved && !isPending

  return <Stack direction={{ xs: 'column-reverse', sm: 'row' }} spacing={2}>
    <Box sx={{ width: "100%" }}>
      <Typography variant="h5"><b>편집기</b></Typography>
      <Form
        schema={{
          ...service.template_schema,
          required: [...service.template_schema.required ?? [], 'template_code'],
          properties: {
            ...service.template_schema.properties,
            template_code: {
              type: 'string',
              title: '템플릿 코드',
              readOnly: template !== undefined,
            },
          },
        }}
        validator={validator}
        formData={state.formData}
        uiSchema={convertTemplateVarToUISchema({ vars: Object.keys(service.template_schema.properties ?? {}) })}
        liveValidate
        focusOnFirstError
        showErrorList="bottom"
        onChange={change}
        onSubmit={submit}
        onError={(errors) => console.log('errors', errors)}
        disabled={isPending}
      >
        <Stack direction="row" spacing={2} sx={{ justifyContent: 'space-between', margin: '0 0 0.5rem 0' }}>
          <Button disabled={isPending} variant="contained" type="submit">{template ? '수정' : '추가'}</Button>
          {
            state.isFormSaved
            ? <Button disabled={!isPreviewAvailable} variant="contained" color="success" onClick={preview}>미리보기</Button>
            : <Tooltip title="템플릿을 먼저 저장해주세요."><Box><Button variant="contained" disabled>미리보기</Button></Box></Tooltip>
          }
        </Stack>
      </Form>
    </Box>
    <Box sx={{ width: "100%" }}>
      <Typography variant="h5"><b>미리보기</b></Typography>
      <div ref={previewRef} style={{ height: '100%' }}></div>
    </Box>
  </Stack>
}

const TemplateManagerTemplateContainer: React.FC<{ service: ServiceDefType, templates: { [k in string]: TemplateDefType } }> = ({ service, templates }) => {
  const queryClient = useQueryClient()
  const deleteTemplateMutation = useDeleteTemplateMutation()
  const [state, setState] = React.useState<{ t?: TemplateDefType }>({})
  const [tabIndex, setTabIndex] = React.useState(0)
  const addSnackbar = (c: string | React.ReactNode, v: VariantType) => enqueueSnackbar(c, getDefaultSnackOption(v))

  const deleteTemplate = () => {
    if (!state.t) return

    deleteTemplateMutation.mutate(
      { service_name: service.name, template_code: state.t.template_code },
      {
        onSuccess: () => {
          setState(ps => ({ ...ps, t: undefined }))
          addSnackbar('템플릿 삭제 완료!', 'success')
          queryClient.invalidateQueries({ queryKey: QUERY_KEYS.LIST_TEMPLATE })
        },
        onError: (error) => addSnackbar(
          <Stack>
            템플릿 삭제 중 문제가 발생했습니다.<br />
            <pre style={{ whiteSpace: 'pre-wrap' }}>{getErrorString(error)}</pre>
          </Stack>,
          'error',
        ),
      }
    )
  }

  const isPending = deleteTemplateMutation.isPending

  return <Stack>
    <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
      <Tabs centered onChange={(_, v) => setTabIndex(v)} value={tabIndex}>
        <Tab label="추가" />
        <Tab label="수정" />
      </Tabs>
    </Box>
    <TabPanel index={0} value={tabIndex}><TemplateEditor service={service} /></TabPanel>
    <TabPanel index={1} value={tabIndex}>
      {
        R.isEmpty(Object.keys(templates))
          ? <Typography>템플릿이 없습니다.</Typography>
          : <Stack>
            <FormControl>
              <InputLabel id="t-t-label">템플릿</InputLabel>
              <Select labelId="t-t-label" id="t-t" label="템플릿" onChange={(e) => setState(ps => ({ ...ps, t: templates[e.target.value as string] }))} value={state.t?.template_code ?? ''}>
                {Object.keys(templates).map((n) => <MenuItem key={n} value={n}>{n}</MenuItem>)}
              </Select>
              {
                state.t && <Box sx={{ display: 'flex', justifyContent: 'end', alignItems: 'center' }}>
                  <Button onClick={deleteTemplate}>템플릿 삭제</Button>
                </Box>
              }
            </FormControl>
            <br />
            {state.t && <TemplateEditor service={service} template={state.t} disabled={isPending} />}
          </Stack>
      }
    </TabPanel>
  </Stack>
}

const TemplateManagerServiceContainer: React.FC<{ services: { [k in string]: ServiceDefType } }> = ({ services }) => {
  const [state, setState] = React.useState<{ s?: ServiceDefType }>({})

  const TemplateManagerTemplateWrapper = wrap
    .ErrorBoundary({ fallback: <Box sx={{ color: 'red' }}>템플릿 목록을 가져오는 중 문제가 발생했습니다,<br />새로고침 해주세요.</Box> })
    .Suspense({ fallback: <CircularProgress /> })
    .on(({ service }: { service: ServiceDefType }) => {
      // eslint-disable-next-line react-hooks/rules-of-hooks
      const { data } = useListTemplatesQuery(service.name)
      return <TemplateManagerTemplateContainer service={service} templates={data.reduce((acc, t) => ({ ...acc, [t.template_code]: t }), {})} />
    })

  return services ? <Stack>
    <FormControl>
      <InputLabel id="t-s-label">서비스</InputLabel>
      <Select labelId="t-s-label" id="t-s" label="서비스" onChange={(e) => setState({ s: services[e.target.value as string] })} value={state.s?.name ?? ''}>
        {Object.keys(services).map((n) => <MenuItem key={n} value={n}>{n}</MenuItem>)}
      </Select>
    </FormControl>
    <br />
    {state.s && <TemplateManagerTemplateWrapper service={state.s} />}
  </Stack> : <></>
}

export const TemplateManagerPage: React.FC = wrap
  .ErrorBoundary({ fallback: <Box sx={{ color: 'red' }}>서비스 목록을 가져오는 중 문제가 발생했습니다,<br />새로고침 해주세요.</Box> })
  .Suspense({ fallback: <CircularProgress /> })
  .on(() => {
    const { data } = useListTemplateManagerServicesQuery()
    return <TemplateManagerServiceContainer services={data.reduce((acc, s) => ({ ...acc, [s.name]: s }), {})} />
  })
