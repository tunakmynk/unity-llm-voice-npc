using System;
using System.IO;
using System.Text;
using UnityEngine;

public static class AudioUtils
{
    const int HEADER_SIZE = 44;

    public static byte[] FromAudioClip(AudioClip clip)
    {
        using (var stream = new MemoryStream())
        {
            using (var writer = new BinaryWriter(stream))
            {
                var samples = new float[clip.samples * clip.channels];
                clip.GetData(samples, 0);

                Int16[] intData = new Int16[samples.Length];
                Byte[] bytesData = new Byte[samples.Length * 2];
                int rescaleFactor = 32767; //to convert float to Int16

                for (int i = 0; i < samples.Length; i++)
                {
                    intData[i] = (short)(samples[i] * rescaleFactor);
                    Byte[] byteArr = new Byte[2];
                    byteArr = BitConverter.GetBytes(intData[i]);
                    byteArr.CopyTo(bytesData, i * 2);
                }

                writer.Write(Encoding.UTF8.GetBytes("RIFF"));
                writer.Write(36 + bytesData.Length);
                writer.Write(Encoding.UTF8.GetBytes("WAVE"));
                writer.Write(Encoding.UTF8.GetBytes("fmt "));
                writer.Write(16);
                writer.Write((ushort)1);
                writer.Write((ushort)clip.channels);
                writer.Write(clip.frequency);
                writer.Write(clip.frequency * clip.channels * 2);
                writer.Write((ushort)(clip.channels * 2));
                writer.Write((ushort)16);
                writer.Write(Encoding.UTF8.GetBytes("data"));
                writer.Write(bytesData.Length);
                writer.Write(bytesData);
            }
            return stream.ToArray();
        }
    }
}
