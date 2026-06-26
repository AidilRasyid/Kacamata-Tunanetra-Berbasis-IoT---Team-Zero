#include <WiFi.h>
#include <HTTPClient.h>

// ================= DEFINISI PIN SENSOR =================
#define TRIG_PIN1 4 
#define ECHO_PIN1 5 

#define TRIG_PIN2 6 
#define ECHO_PIN2 7 

#define TRIG_PIN3 15 
#define ECHO_PIN3 16 

// ================= DEFINISI PIN BUZZER =================
#define BUZZER_PIN1 17 
#define BUZZER_PIN2 18 

// ================= TIMING & STATE =================
unsigned long waktuSebelumnyaKirim = 0;
const long intervalKirim = 2000; // Timer kirim data ke DB setiap 2 detik

// Variabel Pewaktuan Buzzer (Tanpa Delay!)
unsigned long waktuBuzzer1 = 0;
unsigned long waktuBuzzer2 = 0;
bool statusBuzzer1 = LOW;
bool statusBuzzer2 = LOW;

// Variabel Global Jarak
float jarak1 = 999.0;
float jarak2 = 999.0;
float jarak3 = 999.0;

const char* ssid = "MASUKAN NAMA HOSPOT INTERNET";            
const char* password = "MASUKAN PASSWORDNYA";   
const char* serverName = "MASUKAN LINK ADDRESS IPv4 DARI IP CONFIG"; 

// ================= FUNGSI BACA SENSOR =================
float ambilJarak(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  long durasi = pulseIn(echoPin, HIGH, 30000); 
  float jarak = durasi * 0.034 / 2;
  
  if (jarak <= 0 || jarak > 400) {
    return 999.0; // Jika error/jauh, kembalikan 999
  }
  return jarak;
}

// ================= FUNGSI KONTROL BUZZER (NON-BLOCKING) =================
//Membunyikan buzzer tanpa delay yang membekukan program
void kontrolBuzzer(int pinBuzzer, float jarakEfektif, unsigned long &waktuSebelumnya, bool &statusBuzzer) {
  unsigned long waktuSekarang = millis();
  long durasiNyala = 10; // Buzzer nyala sebentar (bunyi bip pendek)
  long durasiMati = 0;

  // Menentukan jeda mati berdasarkan jarak
  if (jarakEfektif <= 30.0) {
    durasiMati = 500;
  } else if (jarakEfektif > 30.0 && jarakEfektif <= 50.0) {
    durasiMati = 2000;
  } else if (jarakEfektif > 50.0 && jarakEfektif <= 70.0) {
    durasiMati = 4000;
  } else {
    // Jika jarak > 70, matikan buzzer sepenuhnya
    digitalWrite(pinBuzzer, LOW);
    statusBuzzer = LOW;
    return;
  }

  // Logika kedip suara (blink) tanpa delay
  if (statusBuzzer == HIGH) {
    if (waktuSekarang - waktuSebelumnya >= durasiNyala) {
      statusBuzzer = LOW;
      waktuSebelumnya = waktuSekarang;
      digitalWrite(pinBuzzer, statusBuzzer);
    }
  } else {
    if (waktuSekarang - waktuSebelumnya >= durasiMati) {
      statusBuzzer = HIGH;
      waktuSebelumnya = waktuSekarang;
      digitalWrite(pinBuzzer, statusBuzzer);
    }
  }
}

void setup() {
  Serial.begin(115200);
  
  pinMode(TRIG_PIN1, OUTPUT); pinMode(ECHO_PIN1, INPUT);
  pinMode(TRIG_PIN2, OUTPUT); pinMode(ECHO_PIN2, INPUT);
  pinMode(TRIG_PIN3, OUTPUT); pinMode(ECHO_PIN3, INPUT);

  pinMode(BUZZER_PIN1, OUTPUT);
  pinMode(BUZZER_PIN2, OUTPUT);

  WiFi.begin(ssid, password);
  Serial.print("Menghubungkan ke WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nTerhubung ke WiFi");
}

void loop() {
  unsigned long waktuSekarang = millis();

  // -----------------------------------------------------------------
  // LOGIKA 1: BACA SENSOR & KIRIM KE DATABASE (Tiap 2 detik)
  // -----------------------------------------------------------------
  if (waktuSekarang - waktuSebelumnyaKirim >= intervalKirim) {
    waktuSebelumnyaKirim = waktuSekarang;

    jarak1 = ambilJarak(TRIG_PIN1, ECHO_PIN1); delay(20); 
    jarak2 = ambilJarak(TRIG_PIN2, ECHO_PIN2); delay(20);
    jarak3 = ambilJarak(TRIG_PIN3, ECHO_PIN3);

    Serial.print("J1: "); Serial.print(jarak1 == 999.0 ? "N/A" : String(jarak1)); Serial.print(" cm | ");
    Serial.print("J2: "); Serial.print(jarak2 == 999.0 ? "N/A" : String(jarak2)); Serial.print(" cm | ");
    Serial.print("J3: "); Serial.println(jarak3 == 999.0 ? "N/A" : String(jarak3));

    if (WiFi.status() == WL_CONNECTED) {
      WiFiClient client;
      HTTPClient http;
      
      http.begin(client, serverName);
      http.addHeader("Content-Type", "application/x-www-form-urlencoded");

      String httpRequestData = "jarak1=" + String(jarak1 == 999.0 ? 0 : jarak1) + 
                               "&jarak2=" + String(jarak2 == 999.0 ? 0 : jarak2) + 
                               "&jarak3=" + String(jarak3 == 999.0 ? 0 : jarak3);

      int httpResponseCode = http.POST(httpRequestData);
      if (httpResponseCode > 0) {
        Serial.print("Data Terkirim, Kode Respon: "); Serial.println(httpResponseCode);
      } else {
        Serial.print("Error kirim DB: "); Serial.println(httpResponseCode);
      }
      http.end();
    } else {
      Serial.println("WiFi terputus, mencoba menghubungkan ulang...");
      WiFi.disconnect();
      WiFi.begin(ssid, password);
    }
  }

  // -----------------------------------------------------------------
  // LOGIKA 2: KONTROL BUZZER 
  // -----------------------------------------------------------------
  
  // Memilih jarak terdekat. Jika Sensor 3 lebih dekat, dia akan mendominasi!
  float jarakEfektifBuzzer1 = min(jarak1, jarak3);
  float jarakEfektifBuzzer2 = min(jarak2, jarak3);

  // Jalankan fungsi pengatur buzzer secara terus menerus (non-blocking)
  kontrolBuzzer(BUZZER_PIN1, jarakEfektifBuzzer1, waktuBuzzer1, statusBuzzer1);
  kontrolBuzzer(BUZZER_PIN2, jarakEfektifBuzzer2, waktuBuzzer2, statusBuzzer2);
}