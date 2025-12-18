export type ReviewStatus = {
  id: string;
  status: string;
  created_at: string;
  updated_at: string;
  metadata: Record<string, unknown>;
};

export type Comment = {
  id: string;
  review_id: string;
  agent_id: string;
  file_path: string;
  line_number: number | null;
  severity: string;
  content: string;
  metadata: Record<string, unknown>;
};

const baseUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const request = async <T,>(path: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(`${baseUrl}${path}`, init);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
};

export const listReviews = async (): Promise<ReviewStatus[]> =>
  request("/api/reviews");

export const createReview = async (diff: string): Promise<{ review: ReviewStatus }> =>
  request("/api/reviews", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ diff })
  });

export const getComments = async (reviewId: string): Promise<Comment[]> =>
  request(`/api/reviews/${reviewId}/comments`);

export const getReview = async (reviewId: string): Promise<ReviewStatus> =>
  request(`/api/reviews/${reviewId}`);

export const indexRepo = async (repoPath: string, includeGlobs: string[]): Promise<{ count: number }> =>
  request("/api/rag/index/repo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_path: repoPath, include_globs: includeGlobs })
  });

export const submitFeedback = async (
  reviewId: string,
  commentId: string,
  rating: number
): Promise<{ status: string }> =>
  request(`/api/reviews/${reviewId}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ comment_id: commentId, rating })
  });

export const getFeedbackSummary = async (
  reviewId: string
): Promise<{ up: number; down: number; neutral: number }> =>
  request(`/api/reviews/${reviewId}/feedback/summary`);

export const getPreferences = async (
  reviewId: string,
  limit = 20
): Promise<{ prompt: string; chosen: string; rejected: string }[]> =>
  request(`/api/reviews/${reviewId}/preferences?limit=${limit}`);

export const getAllPreferences = async (
  limit = 200
): Promise<{ prompt: string; chosen: string; rejected: string }[]> =>
  request(`/api/preferences?limit=${limit}`);

export const resetStore = async (): Promise<{ status: string }> =>
  request("/api/reset", { method: "DELETE" });

export const getOAuthUrl = async (
  provider: "github" | "gitlab"
): Promise<{ url: string }> => request(`/api/auth/${provider}/login`);
