using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using UnityEngine;
using UnityEngine.Events; // Required for Event system
// MRTK Libraries
using Microsoft.MixedReality.Toolkit.UI;
using Microsoft.MixedReality.Toolkit.UI.BoundsControl;

public class MeshReceiver : MonoBehaviour
{
    [Header("TCP Server Settings")]
    public int port = 5555;

    [Header("Mesh Settings")]
    public Transform meshParent;
    public float meshScale = 0.01f;

    [Header("Prefab Settings")]
    [Tooltip("ATTENTION: The BoundsControl component inside this prefab must be unchecked (inactive)!")]
    public GameObject organPrefab;

    [Header("Hierarchy Settings")]
    // Determines which organ (Child) attaches to which organ (Parent).
    // Example: Tumor (9) -> Liver (8)
    public List<HierarchyRule> hierarchyRules = new List<HierarchyRule>()
    {
        new HierarchyRule { childLabel = 9, parentLabel = 8 }
    };

    [System.Serializable]
    public struct HierarchyRule
    {
        public int childLabel;
        public int parentLabel;
    }

    // --- PATIENT DATA STRUCTURES (for JSON) ---
    [System.Serializable]
    public class PatientData
    {
        public PatientInfo hasta;
        public AnalysisResults analiz;
    }

    [System.Serializable]
    public class PatientInfo
    {
        public string ad;
        public string yas;
        public string cinsiyet;
        public string kronik_hastalik;
        public string doktor_notu;
    }

    [System.Serializable]
    public class AnalysisResults
    {
        public float liver_volume_ml;
        public int tumor_count;
        public float total_tumor_volume_ml;
        public List<TumorInfo> tumors;
    }

    [System.Serializable]
    public class TumorInfo
    {
        public int id;
        public float volume_ml;
    }
    // ----------------------------------------

    // Event: To notify the UI script when data is received
    [Header("Events")]
    public UnityEvent<PatientData> OnPatientDataReceived;

    // Memory management
    private Dictionary<int, GameObject> createdOrgans = new Dictionary<int, GameObject>();
    private PatientData currentPatientData;

    // Server state
    public bool isServerRunning = false;
    private TcpListener tcpListener;
    private bool shouldStop = false;

    private Color[] organColors = new Color[]
    {
        Color.red, Color.green, Color.blue, Color.yellow,
        Color.magenta, Color.cyan, new Color(1, 0.5f, 0), Color.gray
    };

    void Start()
    {
        if (meshParent == null) meshParent = this.transform;
        if (organPrefab == null) Debug.LogError("Please assign Organ Prefab from Inspector!");

        StartServer();
    }

    public void StartServer()
    {
        if (isServerRunning) return;
        shouldStop = false;
        StartCoroutine(ListenForConnections());
    }

    public void StopServer()
    {
        shouldStop = true;
        isServerRunning = false;
        if (tcpListener != null) { tcpListener.Stop(); tcpListener = null; }
    }

    IEnumerator ListenForConnections()
    {
        tcpListener = new TcpListener(IPAddress.Any, port);
        tcpListener.Start();
        isServerRunning = true;
        Debug.Log($"TCP Server Started. Port: {port}");

        while (!shouldStop)
        {
            if (tcpListener.Pending())
            {
                TcpClient client = tcpListener.AcceptTcpClient();
                yield return StartCoroutine(HandleClient(client));
            }
            yield return null;
        }
    }

    IEnumerator HandleClient(TcpClient client)
    {
        NetworkStream stream = client.GetStream();

        // STEP 1: RECEIVE PATIENT JSON DATA
        byte[] jsonSizeBuff = new byte[4];
        yield return StartCoroutine(ReadExactly(stream, jsonSizeBuff, 4));
        int jsonSize = IPAddress.NetworkToHostOrder(BitConverter.ToInt32(jsonSizeBuff, 0));

        if (jsonSize > 0)
        {
            byte[] jsonData = new byte[jsonSize];
            yield return StartCoroutine(ReadExactly(stream, jsonData, jsonSize));
            string jsonContent = Encoding.UTF8.GetString(jsonData);

            // Parse JSON and fire Event
            ProcessPatientData(jsonContent);
        }

        // STEP 2: RECEIVE MESH COUNT
        byte[] countBuff = new byte[4];
        yield return StartCoroutine(ReadExactly(stream, countBuff, 4));
        int meshCount = IPAddress.NetworkToHostOrder(BitConverter.ToInt32(countBuff, 0));

        Debug.Log($"Received mesh count: {meshCount}");

        // STEP 3: RECEIVE AND CREATE MESHES ONE BY ONE
        for (int i = 0; i < meshCount; i++)
        {
            // Label
            byte[] lblBuff = new byte[4];
            yield return StartCoroutine(ReadExactly(stream, lblBuff, 4));
            int organLabel = IPAddress.NetworkToHostOrder(BitConverter.ToInt32(lblBuff, 0));

            // File Size
            byte[] sizeBuff = new byte[4];
            yield return StartCoroutine(ReadExactly(stream, sizeBuff, 4));
            int fileSize = IPAddress.NetworkToHostOrder(BitConverter.ToInt32(sizeBuff, 0));

            // Mesh Data (string in OBJ format)
            byte[] objData = new byte[fileSize];
            yield return StartCoroutine(ReadExactly(stream, objData, fileSize));
            string objContent = Encoding.UTF8.GetString(objData);

            // Create Mesh
            CreateMeshFromOBJ(objContent, organLabel);
            yield return null;
        }

        Debug.Log("Data reception completed.");
        client.Close();
    }

    void ProcessPatientData(string jsonContent)
    {
        try
        {
            currentPatientData = JsonUtility.FromJson<PatientData>(jsonContent);
            // Notify UI Script
            OnPatientDataReceived?.Invoke(currentPatientData);
            Debug.Log("Patient data received and UI updated.");
        }
        catch (Exception e)
        {
            Debug.LogError($"JSON Error: {e.Message}");
        }
    }

    IEnumerator ReadExactly(NetworkStream stream, byte[] buffer, int count)
    {
        int totalRead = 0;
        while (totalRead < count)
        {
            if (stream.DataAvailable)
            {
                int read = stream.Read(buffer, totalRead, count - totalRead);
                if (read == 0) break;
                totalRead += read;
            }
            else yield return null;
        }
    }

    void CreateMeshFromOBJ(string objContent, int organLabel)
    {
        // --- A. PARSE OBJ ---
        List<Vector3> vertices = new List<Vector3>();
        List<int> triangles = new List<int>();

        string[] lines = objContent.Split('\n');
        foreach (string line in lines)
        {
            string l = line.Trim();
            if (l.StartsWith("v "))
            {
                string[] p = l.Split(new char[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                float x = float.Parse(p[1], System.Globalization.CultureInfo.InvariantCulture);
                float y = float.Parse(p[2], System.Globalization.CultureInfo.InvariantCulture);
                float z = float.Parse(p[3], System.Globalization.CultureInfo.InvariantCulture);
                vertices.Add(new Vector3(x, z, y) * meshScale);
            }
            else if (l.StartsWith("f "))
            {
                string[] p = l.Split(new char[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                int[] idx = new int[p.Length - 1];
                for (int i = 1; i < p.Length; i++) idx[i - 1] = int.Parse(p[i].Split('/')[0]) - 1;

                if (idx.Length >= 3)
                {
                    triangles.Add(idx[0]); triangles.Add(idx[2]); triangles.Add(idx[1]);
                    if (idx.Length == 4) { triangles.Add(idx[0]); triangles.Add(idx[3]); triangles.Add(idx[2]); }
                }
            }
        }

        Mesh mesh = new Mesh();
        if (vertices.Count > 65000) mesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
        mesh.vertices = vertices.ToArray();
        mesh.triangles = triangles.ToArray();
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();

        // --- B. CREATE PREFAB (SAFE METHOD) ---
        GameObject newOrgan = null;
        if (organPrefab != null)
        {
            // Start inactive so BoundsControl doesn't error
            newOrgan = Instantiate(organPrefab, meshParent);
            newOrgan.SetActive(false);
        }
        else
        {
            newOrgan = new GameObject();
            newOrgan.transform.SetParent(meshParent);
            newOrgan.AddComponent<MeshRenderer>();
        }

        newOrgan.name = $"Organ_{organLabel}";
        newOrgan.transform.localPosition = Vector3.zero;
        newOrgan.transform.localRotation = Quaternion.identity;

        // Assign Mesh and Collider
        MeshFilter mf = newOrgan.GetComponent<MeshFilter>();
        if (mf == null) mf = newOrgan.AddComponent<MeshFilter>();
        mf.mesh = mesh;

        MeshCollider mc = newOrgan.GetComponent<MeshCollider>();
        if (mc == null) mc = newOrgan.AddComponent<MeshCollider>();
        mc.sharedMesh = mesh;
        mc.convex = true; // Required for MRTK interaction

        // Assign Color
        MeshRenderer mr = newOrgan.GetComponent<MeshRenderer>();
        if (mr != null)
            mr.material.color = organColors[(organLabel - 1) % organColors.Length];

        // Add to list
        if (createdOrgans.ContainsKey(organLabel)) createdOrgans[organLabel] = newOrgan;
        else createdOrgans.Add(organLabel, newOrgan);

        // --- C. HIERARCHY SETUP (Tumor -> Liver) ---
        foreach (var rule in hierarchyRules)
        {
            // If new object is Child, check if Parent exists
            if (rule.childLabel == organLabel && createdOrgans.ContainsKey(rule.parentLabel))
            {
                newOrgan.transform.SetParent(createdOrgans[rule.parentLabel].transform);
            }
            // If new object is Parent, check if awaiting Child exists
            else if (rule.parentLabel == organLabel && createdOrgans.ContainsKey(rule.childLabel))
            {
                createdOrgans[rule.childLabel].transform.SetParent(newOrgan.transform);
            }
        }

        // --- D. ACTIVATION ---
        newOrgan.SetActive(true); // Collider is ready, we can activate.

        // Safely enable Bounds Control
        var boundsCtrl = newOrgan.GetComponent<BoundsControl>();
        if (boundsCtrl != null) boundsCtrl.enabled = true;
        else
        {
            var bbox = newOrgan.GetComponent<BoundingBox>();
            if (bbox != null) bbox.enabled = true;
        }
    }

    void OnDestroy() { StopServer(); }
    void OnApplicationQuit() { StopServer(); }
}