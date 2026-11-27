"use client";

import { useParams } from "next/navigation";
import { PurchaseOrderDetail } from "@/features/procurement/PurchaseOrderDetail";

export default function Page() {
  const params = useParams<{ no: string }>();
  return <PurchaseOrderDetail poNo={params.no} />;
}
