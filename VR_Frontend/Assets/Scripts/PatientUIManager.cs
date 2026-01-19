using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;

public class PatientUIManager : MonoBehaviour
{
    [Header("Data Source")]
    public MeshReceiver meshReceiver;

    [Header("UI Text Fields")]
    [Tooltip("Left Side: ID Information")]
    public TextMeshPro textPatientInfo;

    [Tooltip("Right Side: Analysis and List (Combined)")]
    public TextMeshPro textAnalysisInfo;
    // Removed textTumorList variable, no longer needed.

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

        // --- 1. FILL LEFT SIDE (ID) ---
        if (data.hasta != null && textPatientInfo != null)
        {
            textPatientInfo.text = $"<size=120%><b>PATIENT ID CARD</b></size>\n" +
                                   $"--------------------------------\n" + // Dash to avoid unicode issues
                                   $"<b>Name Surname:</b> {data.hasta.ad}\n" +
                                   $"<b>Age:</b> {data.hasta.yas}\n" +
                                   $"<b>Gender:</b> {data.hasta.cinsiyet}\n" +
                                   $"<b>Chronic:</b> {data.hasta.kronik_hastalik}\n\n" +
                                   $"<color=#FFC107><b>Doctor Note:</b></color>\n" +
                                   $"<i>{data.hasta.doktor_notu}</i>";
        }

        // --- 2. FILL RIGHT SIDE (ANALYSIS + LIST COMBINED) ---
        if (data.analiz != null && textAnalysisInfo != null)
        {
            // A) Prepare Analysis Header and Data first
            string combinedText = $"<size=120%><b>ORGAN ANALYSIS</b></size>\n" +
                                  $"--------------------------------\n" +
                                  $"<b>Liver:</b> {data.analiz.liver_volume_ml:F1} ml\n" +
                                  $"<b>Tumor Count:</b> {data.analiz.tumor_count} count\n" +
                                  $"<b>Tumor Load:</b> {data.analiz.total_tumor_volume_ml:F1} ml\n\n";

            // B) Add Space then Tumor List
            combinedText += $"<size=110%><b>TUMOR DETAILS</b></size>\n" +
                            $"--------------------------------\n";

            if (data.analiz.tumors != null && data.analiz.tumors.Count > 0)
            {
                int counter = 0;
                foreach (var tumor in data.analiz.tumors)
                {
                    // Align each line to center
                    combinedText += $"<align=center> Tumor {tumor.id}: <b>{tumor.volume_ml:F1} ml</b></align>\n";

                    // Cut if list is too long (To not overflow the panel)
                    counter++;
                    if (counter >= 8)
                    {
                        combinedText += "<i>...and others</i>";
                        break;
                    }
                }
            }
            else
            {
                combinedText += "No tumor detected.";
            }

            // C) Print All to Screen at Once
            textAnalysisInfo.text = combinedText;
        }
    }
}