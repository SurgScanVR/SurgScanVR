using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;

public class PatientUIManager : MonoBehaviour
{
    [Header("Veri Kaynağı")]
    public MeshReceiver meshReceiver;

    [Header("UI Metin Alanları")]
    [Tooltip("Sol Taraf: Kimlik Bilgileri")]
    public TextMeshPro textPatientInfo;

    [Tooltip("Sağ Taraf: Analiz ve Liste (Birleşik)")]
    public TextMeshPro textAnalysisInfo;
    // textTumorList değişkenini sildik, artık gerek yok.

    private void OnEnable()
    {
        if (meshReceiver != null) meshReceiver.OnPatientDataReceived.AddListener(UpdateUI);
    }

    private void OnDisable()
    {
        if (meshReceiver != null) meshReceiver.OnPatientDataReceived.RemoveListener(UpdateUI);
    }

    public void UpdateUI(MeshReceiver.PatientData data)
    {
        if (data == null) return;

        // --- 1. SOL TARAFI DOLDUR (KİMLİK) ---
        if (data.hasta != null && textPatientInfo != null)
        {
            textPatientInfo.text = $"<size=120%><b>HASTA KİMLİK KARTI</b></size>\n" +
                                   $"--------------------------------\n" + // Unicode hatası için düz tire
                                   $"<b>Ad Soyad:</b> {data.hasta.ad}\n" +
                                   $"<b>Yaş:</b> {data.hasta.yas}\n" +
                                   $"<b>Cinsiyet:</b> {data.hasta.cinsiyet}\n" +
                                   $"<b>Kronik:</b> {data.hasta.kronik_hastalik}\n\n" +
                                   $"<color=#FFC107><b>Doktor Notu:</b></color>\n" +
                                   $"<i>{data.hasta.doktor_notu}</i>";
        }

        // --- 2. SAĞ TARAFI DOLDUR (ANALİZ + LİSTE BİRLEŞİK) ---
        if (data.analiz != null && textAnalysisInfo != null)
        {
            // A) Önce Analiz Başlığını ve Verilerini Hazırla
            string combinedText = $"<size=120%><b>ORGAN ANALİZİ</b></size>\n" +
                                  $"--------------------------------\n" +
                                  $"<b>Karaciğer:</b> {data.analiz.liver_volume_ml:F1} ml\n" +
                                  $"<b>Tümör Sayısı:</b> {data.analiz.tumor_count} adet\n" +
                                  $"<b>Tümör Yükü:</b> {data.analiz.total_tumor_volume_ml:F1} ml\n\n";

            // B) Araya Boşluk Koyup Tümör Listesini Ekle
            combinedText += $"<size=110%><b>TÜMÖR DETAYLARI</b></size>\n" +
                            $"--------------------------------\n";

            if (data.analiz.tumors != null && data.analiz.tumors.Count > 0)
            {
                int counter = 0;
                foreach (var tumor in data.analiz.tumors)
                {
                    // Her satırı sola hizalı yaz
                    combinedText += $"<align=center> Tümör {tumor.id}: <b>{tumor.volume_ml:F1} ml</b></align>\n";

                    // Liste çok uzarsa kes (Panelden taşmasın)
                    counter++;
                    if (counter >= 8)
                    {
                        combinedText += "<i>...ve diğerleri</i>";
                        break;
                    }
                }
            }
            else
            {
                combinedText += "Tümör tespit edilmedi.";
            }

            // C) Hepsini Tek Seferde Ekrana Bas
            textAnalysisInfo.text = combinedText;
        }
    }
}