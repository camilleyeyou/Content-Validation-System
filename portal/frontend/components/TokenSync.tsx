"use client";
import { useEffect } from "react";
import { syncTokenFromUrl } from "@/lib/config";

export default function TokenSync() {
  useEffect(() => {
    syncTokenFromUrl();
  }, []);
  return null;
}
