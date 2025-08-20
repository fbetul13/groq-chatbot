# LLM Karşılaştırma Raporu

## Modeller
- llama-3.1-8b-instant
- llama-3.3-70b-versatile

## Ana Set (base) Sonuçları
- llama-3.1-8b-instant: math=2, turkish=9, coding=8, avg_latency=0.352s
- llama-3.3-70b-versatile: math=4, turkish=10, coding=8, avg_latency=0.244s

## Suite Bazlı Sonuçlar
### domain_specific (soru sayısı: 5)
- llama-3.1-8b-instant: doğru=2/5 (40.0%), avg_latency=0.212s
- llama-3.3-70b-versatile: doğru=3/5 (60.0%), avg_latency=0.243s

### tool_use (soru sayısı: 6)
- llama-3.1-8b-instant: doğru=4/6 (66.7%), avg_latency=0.543s
- llama-3.3-70b-versatile: doğru=6/6 (100.0%), avg_latency=0.324s

### multimodal (soru sayısı: 3)
- llama-3.1-8b-instant: doğru=3/3 (100.0%), avg_latency=0.224s
- llama-3.3-70b-versatile: doğru=3/3 (100.0%), avg_latency=0.178s

### long_context (soru sayısı: 10)
- llama-3.1-8b-instant: doğru=9/10 (90.0%), avg_latency=0.194s
- llama-3.3-70b-versatile: doğru=9/10 (90.0%), avg_latency=0.182s

### consistency (soru sayısı: 4)
- llama-3.1-8b-instant: doğru=2/4 (50.0%), avg_latency=0.229s
- llama-3.3-70b-versatile: doğru=4/4 (100.0%), avg_latency=0.166s

### constrained (soru sayısı: 10)
- llama-3.1-8b-instant: doğru=1/10 (10.0%), avg_latency=0.234s
- llama-3.3-70b-versatile: doğru=1/10 (10.0%), avg_latency=0.17s

## Trend Analizi (Soru Sayısı Artışı)
- tool_use: 2→6 soru | 8B: 2→4, 70B: 2→6
- multimodal: 1→3 soru | 8B: 1→3, 70B: 1→3
- long_context: 1→3→10 soru | 8B: 0→0→9, 70B: 0→0→9
- consistency: 2→4 soru | 8B: 1→2, 70B: 2→4
- constrained: 3→10 soru | 8B: 0→1, 70B: 0→1

## Ek Metrikler
- Deterministiklik (3 tekrar): 8B 30/30, 70B 28/30
- TPS (yaklaşık): 8B ~70.9±97.2, 70B ~75.6±90.3
- Biçim uyumu (base): 8B 25/30, 70B 22/30

## Maliyet (örnek hesap için toplam token: input≈2748, output≈633)
- 8B (Groq in $0.05/M, out $0.08/M): ~ $0.000188
- 70B Versatile (Groq in $0.59/M, out $0.79/M): ~ $0.002121
