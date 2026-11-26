"use client";

import { useParams } from "next/navigation";
import { StockRequestDetail } from "@/features/stock-requests/StockRequestDetail";

export default function Page() {
  const params = useParams<{ no: string }>();
  return <StockRequestDetail stockRequestNo={params.no} />;
}
