import axios from 'axios'
import type { AnalysisResponse, BatchResponse } from '../types/analysis'

const baseURL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api'

const client = axios.create({ baseURL })

export class ApiError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

function unwrapError(error: unknown): never {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    throw new ApiError(typeof detail === 'string' ? detail : error.message)
  }
  throw error as Error
}

export async function uploadImage(file: File): Promise<AnalysisResponse> {
  const form = new FormData()
  form.append('file', file)
  try {
    const { data } = await client.post<AnalysisResponse>('/analyze', form)
    return data
  } catch (error) {
    unwrapError(error)
  }
}

export async function uploadBatch(files: File[]): Promise<BatchResponse> {
  const form = new FormData()
  files.forEach((file) => form.append('files', file))
  try {
    const { data } = await client.post<BatchResponse>('/analyze/batch', form)
    return data
  } catch (error) {
    unwrapError(error)
  }
}

export async function getBatch(batchId: string): Promise<BatchResponse> {
  try {
    const { data } = await client.get<BatchResponse>(`/batch/${batchId}`)
    return data
  } catch (error) {
    unwrapError(error)
  }
}

export async function getAnalysis(analysisId: string): Promise<AnalysisResponse> {
  try {
    const { data } = await client.get<AnalysisResponse>(`/analyze/${analysisId}`)
    return data
  } catch (error) {
    unwrapError(error)
  }
}

export async function correctInstructor(
  analysisId: string,
  x: number,
  y: number,
): Promise<AnalysisResponse> {
  try {
    const { data } = await client.patch<AnalysisResponse>(`/analyze/${analysisId}/instructor`, { x, y })
    return data
  } catch (error) {
    unwrapError(error)
  }
}

export async function correctSeat(
  analysisId: string,
  seatId: string,
  body: { occupied?: boolean; delete?: boolean },
): Promise<AnalysisResponse> {
  try {
    const { data } = await client.patch<AnalysisResponse>(`/analyze/${analysisId}/seats/${seatId}`, body)
    return data
  } catch (error) {
    unwrapError(error)
  }
}

export async function correctBoard(analysisId: string, x: number, y: number): Promise<AnalysisResponse> {
  try {
    const { data } = await client.patch<AnalysisResponse>(`/analyze/${analysisId}/board`, { x, y })
    return data
  } catch (error) {
    unwrapError(error)
  }
}

export async function moveSeat(
  analysisId: string,
  seatId: string,
  x: number,
  y: number,
): Promise<AnalysisResponse> {
  try {
    const { data } = await client.patch<AnalysisResponse>(`/analyze/${analysisId}/seats/${seatId}/move`, { x, y })
    return data
  } catch (error) {
    unwrapError(error)
  }
}

export async function createSeat(
  analysisId: string,
  bbox: { x1: number; y1: number; x2: number; y2: number },
): Promise<AnalysisResponse> {
  try {
    const { data } = await client.post<AnalysisResponse>(`/analyze/${analysisId}/seats`, bbox)
    return data
  } catch (error) {
    unwrapError(error)
  }
}

export async function deleteAnalysis(analysisId: string): Promise<void> {
  try {
    await client.delete(`/analyze/${analysisId}`)
  } catch (error) {
    unwrapError(error)
  }
}

export interface ExportResult {
  image_path: string
  label_path: string
  seat_count: number
  instructor_included: boolean
}

export async function exportTrainingData(analysisId: string): Promise<ExportResult> {
  try {
    const { data } = await client.post<ExportResult>(`/analyze/${analysisId}/export`)
    return data
  } catch (error) {
    unwrapError(error)
  }
}
