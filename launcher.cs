using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

namespace QuickFind
{
    static class Program
    {
        [STAThread]
        static void Main()
        {
            string appDir = Path.GetDirectoryName(Application.ExecutablePath);
            string projectDir = Path.Combine(appDir, "QuickFind");
            if (!Directory.Exists(projectDir))
            {
                projectDir = appDir;
            }

            // Check if full PyInstaller executable is present
            string distExe = Path.Combine(projectDir, "dist", "QuickFind.exe");
            if (File.Exists(distExe) && !string.Equals(distExe, Application.ExecutablePath, StringComparison.OrdinalIgnoreCase))
            {
                Process.Start(new ProcessStartInfo
                {
                    FileName = distExe,
                    WorkingDirectory = projectDir,
                    UseShellExecute = true
                });
                return;
            }

            // Find Python executable
            string pythonw = FindPython();
            string mainPy = Path.Combine(projectDir, "main.py");

            if (string.IsNullOrEmpty(pythonw) || !File.Exists(mainPy))
            {
                MessageBox.Show(
                    "QuickFind requires Python 3 to be installed.\n\nLooking for:\n" + mainPy,
                    "QuickFind Launcher",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Warning
                );
                return;
            }

            // Launch Python script with hidden console window
            ProcessStartInfo psi = new ProcessStartInfo
            {
                FileName = pythonw,
                Arguments = "\"" + mainPy + "\"",
                WorkingDirectory = projectDir,
                UseShellExecute = false,
                CreateNoWindow = true,
                WindowStyle = ProcessWindowStyle.Hidden
            };

            try
            {
                Process.Start(psi);
            }
            catch (Exception ex)
            {
                MessageBox.Show("Failed to launch QuickFind:\n" + ex.Message, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        static string FindPython()
        {
            string[] searchPaths = new string[]
            {
                @"C:\Program Files\Python312\pythonw.exe",
                @"C:\Program Files\Python312\python.exe",
                @"C:\Program Files\Python311\pythonw.exe",
                @"C:\Program Files\Python310\pythonw.exe",
                Environment.ExpandEnvironmentVariables(@"%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"),
                Environment.ExpandEnvironmentVariables(@"%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe"),
                "pythonw.exe",
                "python.exe"
            };

            foreach (string p in searchPaths)
            {
                if (File.Exists(p)) return p;
            }

            return "pythonw.exe";
        }
    }
}
