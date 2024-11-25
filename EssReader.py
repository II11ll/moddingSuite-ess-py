import struct
import io
from numba import jit

@jit(nopython=True)
def compute_sample1(inputs, vv21, v14):
    return inputs + ((vv21 * v14 + 128) >> 8)
class EssReader:
    @staticmethod
    def write_wav_header(bw, channels, samplerate, bytes):
        bw.write(b"RIFF")
        bw.write(struct.pack("<i", bytes + 36))
        bw.write(b"WAVE")
        bw.write(b"fmt ")
        bw.write(struct.pack("<i", 16))
        bw.write(struct.pack("<h", 1))
        bw.write(struct.pack("<h", channels))
        bw.write(struct.pack("<i", samplerate))
        bw.write(struct.pack("<i", samplerate * channels * 2))
        bw.write(struct.pack("<h", channels * 2))
        bw.write(struct.pack("<h", 16))
        bw.write(b"data")
        bw.write(struct.pack("<i", bytes))

    @staticmethod
    def swap(le):
        b1 = le & 0xFF
        b2 = (le >> 8) & 0xFF
        b3 = (le >> 16) & 0xFF
        b4 = (le >> 24) & 0xFF
        return b1 * 16777216 + b2 * 65536 + b3 * 256 + b4
    @staticmethod
    def read_ess(data):
        with io.BytesIO(data) as in_ms:
            br = in_ms

            with io.BytesIO() as ms:
                bw = ms

                br.read(4)  # skip ESS version
                unk = struct.unpack("<B", br.read(1))[0]
                channels = struct.unpack("<B", br.read(1))[0]
                samplerate = struct.unpack("<B", br.read(1))[0] * 256 + struct.unpack("<B", br.read(1))[0]
                num_samples = EssReader.swap(struct.unpack("<I", br.read(4))[0])
                br.read(4)
                br.read(4)  # num_samples again

                EssReader.write_wav_header(bw, channels, samplerate, num_samples * channels * 2)

                nfr = 1
                # dumb end search
                while in_ms.tell() + EssReader.swap(struct.unpack("<I", br.read(4))[0]) + 4 < len(data):
                    nfr += 1
                datapos = in_ms.tell()

                in_ms.seek(0x14)

                frs = [0] * (nfr + 1)
                frs[0] = 0
                audio = [0] * 1024
                os = [0] * 1024
                print('init frs')
                for j in range(nfr):
                    frs[j + 1] = EssReader.swap(struct.unpack("<I", br.read(4))[0])
                
                for j in range(nfr):
                    fr_size = frs[j + 1] - frs[j] - 20 * channels
                    frame = br.read(fr_size)
                    fr_samples = num_samples
                    if fr_samples > 1024:
                        fr_samples = 1024

                    sample, sample1, sample2, input, output = 0, 0, 0, 0, 0
                    vv10, vv20, vv21, vv22 = 0, 0, 0, 0
                    v6, v16, v17, v18, v19, v26, v27, v31, v34, v35, v39 = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
                    Bitvalue, Result, Bit16 = 0, 0, 0
                    C1, C2, C3 = 0, 0, 0

                    in_ms.seek(datapos + frs[j] + 20 * channels)
                    frame = br.read(fr_size)
                    in_ms.seek(datapos + frs[j])

                    vv20 = (struct.unpack("<b", br.read(1))[0] << 8) | struct.unpack("<B", br.read(1))[0]
                    vv21 = (struct.unpack("<b", br.read(1))[0] << 8) | struct.unpack("<B", br.read(1))[0]
                    output = (struct.unpack("<b", br.read(1))[0] << 8) | struct.unpack("<B", br.read(1))[0]
                    vv22 = (struct.unpack("<b", br.read(1))[0] << 8) | struct.unpack("<B", br.read(1))[0]
                    sample1 = (struct.unpack("<b", br.read(1))[0] << 8) | struct.unpack("<B", br.read(1))[0]
                    sample2 = (struct.unpack("<b", br.read(1))[0] << 8) | struct.unpack("<B", br.read(1))[0]
                    vv10 = (struct.unpack("<b", br.read(1))[0] << 8) | struct.unpack("<B", br.read(1))[0]
                    C1 = (struct.unpack("<b", br.read(1))[0] << 8) | struct.unpack("<B", br.read(1))[0]
                    C2 = (struct.unpack("<b", br.read(1))[0] << 8) | struct.unpack("<B", br.read(1))[0]
                    C3 = (struct.unpack("<b", br.read(1))[0] << 8) | struct.unpack("<B", br.read(1))[0]

                    # region phase 1 left

                    bb, bn = 0, 0
                    bprev = -1
                    i = 0
                    #print('i < fr_samples')
                    while i < fr_samples:
                        bb = (frame[bn // 8] >> (7 - bn % 8)) & 1
                        if bb > 0:
                            v6 = 0
                            Bitvalue = bn - bprev - 1
                            bprev = bn
                            if Bitvalue >= 2:
                                if Bitvalue >= 4:
                                    if Bitvalue >= 6:
                                        if Bitvalue == 24:  # take 16 bits from stream
                                            Bit16 = 0
                                            for k in range(16):
                                                bn += 1
                                                Bit16 = Bit16 * 2 + ((frame[bn // 8] >> (7 - bn % 8)) & 1)  # 1 bit
                                                bprev += 1
                                            Bitvalue = Bit16 + 24  # add them
                                        v26 = C3
                                        v27 = C2
                                        v6 = C1 + v27 + (v26 + 1) * ((Bitvalue >> 1) - 2)
                                        v39 = v26 + v6
                                        C1 += 6 * ((C1 + 2048) // 2048)
                                        C2 = v27 + 6 * ((v27 + 1024) // 1024)
                                        C3 = v26 + 6 * ((v26 + 512) // 512)
                                    else:
                                        v18 = C2
                                        v19 = C3
                                        v6 = v18 + C1
                                        v39 = v19 + v6
                                        C1 += 6 * ((C1 + 2048) // 2048)
                                        C2 = v18 + 6 * ((v18 + 1024) // 1024)
                                        C3 = v19 - 2 * ((v19 + 510) // 512)
                                else:
                                    v6 = C1
                                    v17 = C2
                                    v39 = v17 + C1
                                    C1 = v6 + 6 * ((v6 + 2048) // 2048)
                                    C2 = v17 - 2 * ((v17 + 1022) // 1024)
                                v16 = v39
                            else:
                                v16 = C1
                                C1 -= 2 * ((C1 + 2046) // 2048)
                            Result = (v16 + v6) >> 1

                            # C1-2-3 correction
                            if Result > C1:
                                if Result > C2:
                                    if Result <= C3:
                                        C3 = C3 - 2 * ((C3 + 510) // 512)
                                    else:
                                        pass
                                else:
                                    C2 = C2 - 2 * ((C2 + 1022) // 1024)
                            else:
                                C1 -= 2 * ((C1 + 2046) // 2048)

                            v31 = v16 - v6
                            if v31 > 0x40:  # ???
                                v34 = v31 // 4 + 1

                                # take 2 bits from stream
                                bn += 1
                                bb = (frame[bn // 8] >> (7 - bn % 8)) & 1  # 1st
                                bn += 1
                                v35 = bb * 2 + ((frame[bn // 8] >> (7 - bn % 8)) & 1)  # 2nd
                                bprev += 2

                                Result = v6 + v34 * v35

                            if (Bitvalue & 1) > 0:
                                Result = ~Result  # sign

                            os[i] = Result
                            i += 1
                        bn += 1
                        

                    # endregion

                    v14, v28, v12 = 0, 0, 0

                    # region phase 2 left
                    #print('for i in range(fr_samples)')
                    for i in range(fr_samples):
                        
                        input = os[i]

                        v18 = output

                        v14 = 2 * (2 * sample1 - vv10) - 5 * sample2
                        v12 = 2 * output - vv22
                        v28 = sample2
                        sample2 = sample1
                        # 不知道为啥，但这段代码在i大于500多时会非常慢...改成numba就好了
                        #sample1 = input + ((vv21 * v14 + 128) >> 8)
                        sample1 = compute_sample1(input, vv21, v14)
                        # the meaning of this stuff:
                        # d=2
                        # if (v14 < 0) d=-d
                        # if (input < 0) d=-d
                        if (v14 | input) != 0:
                            vv21 += ((v14 ^ input) & -0x20000001 | 0x40000000) >> 29
                        sample = sample1 + ((vv20 * v12 + 128) >> 8)
                        if sample > 32767:
                            sample = 32767
                        if sample < -32768:
                            sample = -32768
                        if (sample1 | v12) != 0:
                            vv20 += ((sample1 ^ v12) & -0x20000001 | 0x40000000) >> 29

                        vv22 = v18
                        # output = (output + 7 * sample) / 8
                        output = sample

                        audio[i] = output

                        vv10 = v28
                    # endregion

                    # for i in range(512): Console.WriteLine(audio[i].ToString("X8"))
                    #print('for i in range(fr_samples)')
                    for i in range(fr_samples):
                        bw.write(struct.pack("<h", audio[i]))

                    num_samples -= fr_samples

                #bw.close()
                #in_ms.close()
                with open('audio.txt', 'w' , encoding='utf-8') as f:
                    f.write(str(audio))
                return bw.getvalue()


with open('alerte.ess', 'rb') as file, open('test.wav', 'wb') as f2:
    byte_array = file.read()
    ess_reader = EssReader()
    result = bytes(ess_reader.read_ess(byte_array))
    f2.write(result)
    f2.flush()

