using System;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;

class Program
{
    public static int CalculateMD5(string name)
    {
        return BitConverter.ToInt32(MD5.Create().ComputeHash(Encoding.UTF8.GetBytes(name)), 0);
    }

    static void Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("Usage: extract_types.exe <path_to_dll>");
            return;
        }

        string dllPath = args[0];

        if (!File.Exists(dllPath))
        {
            Console.WriteLine($"Error: File '{dllPath}' not found.");
            return;
        }

        Assembly assembly = Assembly.LoadFrom(dllPath);
        using (StreamWriter writer = new StreamWriter("type_ids.txt"))
        {
            foreach (Type type in assembly.GetTypes())
            {
                string name = type.FullName;
                int hash = CalculateMD5(name);
                writer.WriteLine($"{hash} {name}");
            }
        }
    }
}