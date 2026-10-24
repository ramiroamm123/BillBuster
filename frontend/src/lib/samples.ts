import type { AuditResult } from "@/lib/types";

export interface SampleInvoice {
  id: string;
  label: string;
  imagePath: string;
  fileName: string;
  result: AuditResult;
}

export const SAMPLES: SampleInvoice[] = [
  {
    id: "hidden-tip",
    label: "Factura con propina no informada",
    imagePath: "/samples/receipt-hidden-tip.png",
    fileName: "receipt-hidden-tip.png",
    result: {
      merchant: "La Parrilla del Centro",
      total_billed: "$225.66",
      real_subtotal: "$158.00",
      risk_level: "ALTO",
      summary:
        "La cuenta incluye un Pisco sour duplicado, un subtotal inflado y un cargo por servicio del 18% añadido sin aviso. En total se cobran $67.66 por encima del consumo real de $158.00.",
      suspicious_charges: [
        {
          item: "Pisco sour (2ª línea)",
          amount: "$22.00",
          reason: "Ítem idéntico cobrado dos veces; en la mesa se pidió solo uno.",
        },
        {
          item: "Subtotal impreso",
          amount: "$7.00",
          reason: "Las líneas suman $180.00, pero el subtotal impreso es $187.00.",
        },
        {
          item: "Cargo por servicio 18%",
          amount: "$33.66",
          reason: "Propina incluida automáticamente sin aviso previo y calculada sobre un subtotal inflado.",
        },
        {
          item: "Fee de mesa",
          amount: "$5.00",
          reason: "Cargo ambiguo no informado en la carta ni justificado en la cuenta.",
        },
      ],
      dispute_message:
        "Buenas noches. Al revisar la cuenta de la mesa 12 he encontrado algunas discrepancias que les agradecería corregir:\n\n1. El Pisco sour aparece cobrado dos veces ($22.00), pero solo pedimos uno.\n2. Las líneas suman $180.00, mientras que el subtotal impreso es $187.00 (diferencia de $7.00).\n3. Se ha incluido un cargo por servicio del 18% ($33.66) del que no se nos informó; preferimos decidir la propina voluntariamente.\n4. El \"Fee de mesa\" ($5.00) no figura en la carta.\n\nEl consumo real asciende a $158.00. ¿Podrían emitir una cuenta corregida? Muchas gracias.",
    },
  },
  {
    id: "ok",
    label: "Factura correcta",
    imagePath: "/samples/receipt-ok.png",
    fileName: "receipt-ok.png",
    result: {
      merchant: "Café Aurora",
      total_billed: "$20.90",
      real_subtotal: "$19.00",
      risk_level: "BAJO",
      summary:
        "Los importes de cada línea, el subtotal de $19.00 y el IVA del 10% ($1.90) están correctamente calculados. No se detectaron propinas impuestas ni cargos ocultos.",
      suspicious_charges: [],
      dispute_message:
        "No es necesario presentar ningún reclamo: la cuenta es correcta. Si lo desea, puede dejar una propina voluntaria, ya que no está incluida.",
    },
  },
];

export async function loadSampleFile(sample: SampleInvoice): Promise<File> {
  const res = await fetch(sample.imagePath);
  if (!res.ok) throw new Error(`No se pudo cargar la imagen de ejemplo (${res.status}).`);
  const blob = await res.blob();
  return new File([blob], sample.fileName, { type: blob.type || "image/png" });
}
