"use client";

import { useParams } from "next/navigation";
import AdminAssessmentDetailRoute from "@/components/admin/AdminAssessmentDetailRoute";

export default function AdminAssessmentDetailPage() {
  const params = useParams<{ submissionId: string }>();
  const submissionId = Number(params.submissionId);

  if (!Number.isInteger(submissionId) || submissionId < 1) {
    return <main className="grid h-[100dvh] place-items-center bg-[#f6f8fc] px-6 text-sm text-slate-600">Invalid assessment identifier.</main>;
  }

  return <AdminAssessmentDetailRoute submissionId={submissionId} />;
}
