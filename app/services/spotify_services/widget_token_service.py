# =============================================================================
# Widget Token Servis Modülü (Widget Token Service Module)
# =============================================================================
# Bu modül, uygulama içi widget'lar (örn: Spotify "Şu An Çalan" widget'ı)
# için güvenli token'lar oluşturma, doğrulama ve bu token'lardan bilgi
# (kullanıcı adı, widget yapılandırması) çıkarma işlemlerini yöneten bir
# servis sınıfı (WidgetTokenService) içerir. Token'lar, kullanıcıya özel
# widget erişimini ve yapılandırmasını güvenli bir şekilde sağlamak için kullanılır.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#      : Gerekli Python modüllerinin (secrets, base64, json, time, datetime)
#        içe aktarılması.
# 2.0  WIDGET TOKEN SERVİS SINIFI (WIDGET TOKEN SERVICE CLASS)
#      2.1. WidgetTokenService
#           : Widget token işlemlerini yöneten ana servis sınıfı.
#           2.1.1.  __init__()
#                   : Başlatıcı metot. Token geçerlilik süresini ayarlar.
#           2.1.2.  generate_widget_token(username, widget_config)
#                   : Belirtilen kullanıcı ve widget yapılandırması için güvenli bir widget token'ı oluşturur.
#           2.1.3.  validate_widget_token(token)
#                   : Verilen widget token'ının geçerliliğini (süre sonu vb.) kontrol eder ve payload'u çıkarır.
#           2.1.4.  get_widget_token(token)
#                   : Geçerli bir widget token'ından widget'a özel yapılandırma bilgilerini çıkarır.
#           2.1.5   get_or_create_widget_token(username, widget_config)
#                   : Belirtilen kullanıcı ve widget yapılandırması için güvenli bir widget token'ı oluşturur.
#                       Eğer token mevcut ise onu döndürür.
#           2.1.6   get_widget_config_from_token(token)
#                   : Geçerli bir widget token'ından widget yapılandırma bilgilerini çıkarır.
#           2.1.7   get_username_from_token(token)
#                   : Geçerli bir widget token'ından kullanıcı adını çıkarır.
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import secrets      # Güvenli rastgele sayılar ve token'lar üretmek için
import string       # Base62 karakter seti için
import base64       # Base64 encode/decode işlemleri için
import json         # JSON verilerini serialize/deserialize etmek için
import time         # Zaman damgaları için (Unix timestamp)
from datetime import datetime, timedelta # Tarih ve zaman işlemleri, süreler için
from typing import Dict, Any, Optional, Tuple # Tip ipuçları için
from app.database.spotify_user_repository import SpotifyUserRepository
from app.database.spotify_widget_repository import SpotifyWidgetRepository

# =============================================================================
# 2.0 WIDGET TOKEN SERVİS SINIFI (WIDGET TOKEN SERVICE CLASS)
# =============================================================================
class WidgetTokenService:
    """
    Widget'lar için güvenli erişim token'ları oluşturma, doğrulama ve
    bu token'lardan bilgi çıkarma işlemlerini yönetir.
    """

    # -------------------------------------------------------------------------
    # 2.1.1. __init__() : Başlatıcı metot.
    # -------------------------------------------------------------------------
    def __init__(self, token_validity_days: int = 30):
        """
        WidgetTokenService sınıfının başlatıcı metodu.

        Args:
            token_validity_days (int, optional): Oluşturulan widget token'larının
                                                 kaç gün geçerli olacağını belirtir.
                                                 Varsayılan değer 30 gündür.
        """
        self.token_validity_days: int = token_validity_days
        # print(f"WidgetTokenService örneği oluşturuldu. Token geçerlilik süresi: {self.token_validity_days} gün.") # Geliştirme için log

    # -------------------------------------------------------------------------
    # 2.1.2. generate_widget_token(...) : Güvenli bir widget token oluşturur.
    # -------------------------------------------------------------------------
    def generate_widget_token(self, username: str, length: int = 12) -> str:
        """
        Belirtilen kullanıcı adı için belirtilen uzunlukta bir base62 token oluşturur.

        Args:
            username (str): Token'ın ilişkilendirileceği kullanıcının adı.
                            Bu parametre şu anda doğrudan token üretimine dahil edilmese de,
                            gelecekteki olası genişletmeler veya loglama için tutulmuştur.
            length (int): Oluşturulacak token'ın uzunluğu. Varsayılan değer 12'dir.

        Returns:
            str: Oluşturulan base62 token.

        Raises:
            ValueError: Kullanıcı adı sağlanmazsa.
            RuntimeError: Token oluşturma sırasında beklenmedik bir hata oluşursa.
        """
        if not username:
            print("Kullanıcı adı sağlanmazsa.")
            raise ValueError("Kullanıcı adı gereklidir.")

        try:
            # Base62 karakter setini tanımla (rakamlar + küçük harfler + büyük harfler)
            alphabet = string.digits + string.ascii_letters
            # Belirtilen uzunlukta güvenli rastgele karakterler seçerek token oluştur
            token = ''.join(secrets.choice(alphabet) for _ in range(length))
            return token
        except Exception as e:
            # Token oluşturma sırasında beklenmedik bir hata oluşursa
            # Daha genel bir hata mesajı ile RuntimeError yükselt
            # Orijinal hatayı da zincirleme hata olarak ekle (debugging için faydalı)
            raise RuntimeError(f"Token oluşturulamadı: {str(e)}") from e
    # -------------------------------------------------------------------------
    # 2.1.3. generate_and_insert_widget_token(...) : Widget token'ını oluşturur ve veritabanına kaydeder.
    # -------------------------------------------------------------------------
    def generate_and_insert_widget_token(self, username: str) -> Optional[str]:
        """
        Belirtilen kullanıcı için yeni bir widget token'ı oluşturur ve veritabanına kaydeder.
        Veriyi sözlük olarak gönderir.

        Args:
            username (str): Token'a sahip olacak kullanıcının adı.

        Returns:
            Optional[str]: Yeni oluşturulan widget token'ı.
        """
        token = self.generate_widget_token(username)
        widget_name = "Unknown"  # Varsayılan veya daha sonra güncellenecek
        widget_type = "Unknown"  # Varsayılan veya daha sonra güncellenecek
        config_data = "{}"       # JSON string olarak varsayılan konfigürasyon
        spotify_user_id = SpotifyUserRepository().spotify_get_user_data(username)['spotify_user_id']

        token_data: Dict[str, Any] = {
            "beatify_username": username,
            "widget_token": token,
            "widget_name": widget_name,
            "widget_type": widget_type,
            "config_data": config_data,
            "spotify_user_id": spotify_user_id
        }

        # SpotifyWidgetRepository örneğini oluşturup metodu çağırın
        # (SpotifyWidgetRepository'nin nasıl başlatıldığına bağlı olarak düzenleyin)
        # spotify_repo = SpotifyWidgetRepository() # Eğer bağlantı vs. gerekiyorsa uygun şekilde başlatın
        # spotify_repo.spotify_store_widget_token(token_data)

        # Şimdilik doğrudan çağırdığınızı varsayıyorum:
        SpotifyWidgetRepository().spotify_store_widget_token(token_data)
        
        return token
    # -------------------------------------------------------------------------
    # 2.1.4. validate_widget_token(...) : Widget token'ını doğrular ve payload'u çıkarır.
    # -------------------------------------------------------------------------
    def validate_widget_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verilen widget token'ının geçerliliğini kontrol eder.
        
        Token iki formatta olabilir:
        1. Kısa token (12 karakter) - Bu durumda veritabanından tam payload alınır
        2. Tam token (Base64 URL-safe encode edilmiş) - Doğrudan decode edilir
        
        Her iki durumda da son kullanma tarihi kontrolü yapılır.

        Args:
            token (str): Doğrulanacak widget token'ı (kısa veya tam format).

        Returns:
            Tuple[bool, Optional[Dict[str, Any]]]:
                - İlk eleman (bool): Token geçerliyse True, değilse False.
                - İkinci eleman (Optional[Dict[str, Any]]): Token geçerliyse
                  decode edilmiş payload (sözlük), değilse None.
        """
        if not token or not isinstance(token, str):
            return False, None
            
        # Kısa token kontrolü (12 karakter civarı)
        if len(token) <= 16:  # Kısa token muhtemelen 16 karakterden kısa olacak
            try:
                # Veritabanından kısa token ile tam token verisini al
                db = SpotifyWidgetRepository()
                full_token_data = db.spotify_get_widget_token_by_short_token(token)
                
                if not full_token_data:
                    return False, None  # Kısa token veritabanında bulunamadı
                    
                # JSON parse etme
                payload: Dict[str, Any] = json.loads(full_token_data)
                
                # Gerekli alanların varlığını kontrol et
                required_fields = ['username', 'iat', 'exp', 'widget_config', 'nonce']
                if not all(field in payload for field in required_fields):
                    return False, None
                
                # Son kullanma tarihini kontrol et
                current_timestamp: int = int(time.time())
                if current_timestamp > payload.get('exp', 0):
                    return False, None  # Token süresi dolmuş
                    
                return True, payload
                
            except Exception as e:
                print(f"Kısa widget token doğrulanırken hata: {str(e)}")
                return False, None
        
        # Tam token kontrolü (Base64 URL-safe encode edilmiş)
        try:
            # Base64 decode etme
            try:
                decoded_payload_bytes: bytes = base64.urlsafe_b64decode(token.encode('utf-8'))
            except base64.binascii.Error:  # type: ignore[attr-defined]
                return False, None
                
            decoded_payload_str: str = decoded_payload_bytes.decode('utf-8')
            
            # JSON parse etme
            payload: Dict[str, Any] = json.loads(decoded_payload_str)

            # Gerekli alanların varlığını kontrol et
            required_fields = ['username', 'iat', 'exp', 'widget_config', 'nonce']
            if not all(field in payload for field in required_fields):
                return False, None

            # Son kullanma tarihini kontrol et
            current_timestamp: int = int(time.time())
            if current_timestamp > payload.get('exp', 0):
                return False, None  # Token süresi dolmuş

            return True, payload
            
        except json.JSONDecodeError:
            return False, None
        except UnicodeDecodeError:
            return False, None
        except Exception as e:  # Diğer beklenmedik hatalar
            print(f"Widget token doğrulanırken genel bir hata oluştu: {str(e)}")
            return False, None

    # -------------------------------------------------------------------------
    # 2.1.5. get_widget_token(...) : Token'dan widget token'ını çıkarır.
    # -------------------------------------------------------------------------
    def get_widget_token(self, username: str) -> Optional[str]:
        """
        Belirtilen kullanıcı için mevcut widget token'ını veritabanından alır.

        Args:
            username (str): Token'a sahip kullanıcının adı.

        Returns:
            Optional[str]: Kullanıcının widget token'ı varsa token, yoksa None.
        """
        db = SpotifyWidgetRepository()
        token = db.spotify_get_widget_token(username)
        return token

    # -------------------------------------------------------------------------
    # 2.1.6. get_or_create_widget_token(...) : Token'dan widget token'ını çıkarır.
    # -------------------------------------------------------------------------
    def get_or_create_widget_token(self, username: str) -> Optional[str]:
        """
        Belirtilen kullanıcı için mevcut widget token'ını alır veya yoksa yeni bir token oluşturur.

        Args:
            username (str): Token'a sahip olacak kullanıcının adı.

        Returns:
            Optional[str]: Mevcut veya yeni oluşturulan widget token'ı.
        """
        # Önce mevcut token'ı kontrol et
        existing_token = self.get_widget_token(username)
        if existing_token:
            print("Mevcut token bulundu. existing_token: ", existing_token)
            return existing_token
        
        # Yeni token oluştur ve döndür
        return self.generate_and_insert_widget_token(username)
    
    # -------------------------------------------------------------------------
    # 2.1.7. get_widget_config_from_token(...) : Token'dan widget yapılandırmasını çıkarır.
    # -------------------------------------------------------------------------
    def get_widget_config_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Geçerli bir widget token'ından widget'a özel yapılandırma bilgilerini çıkarır.

        Args:
            token (str): Bilgilerin çıkarılacağı widget token'ı.

        Returns:
            Optional[Dict[str, Any]]: Token geçerliyse widget yapılandırma sözlüğü,
                                      değilse None.
        """
        # print(f"Token'dan widget yapılandırması alınıyor: {token[:20]}...") # Geliştirme için log
        is_valid, payload = self.validate_widget_token(token)
        if not is_valid or not payload:
            # print("Token geçersiz, yapılandırma alınamadı.") # Geliştirme için log
            return None
        
        widget_config = payload.get('widget_config')
        # if widget_config:
            # print(f"Widget yapılandırması başarıyla alındı: {widget_config}") # Geliştirme için log
        # else:
            # print("Token payload'unda widget yapılandırması bulunamadı.") # Geliştirme için log
        return widget_config

    # -------------------------------------------------------------------------
    # 2.1.8. get_username_from_token(...) : Token'dan kullanıcı adını çıkarır.
    # -------------------------------------------------------------------------
    def get_username_from_token(self, token: str) -> Optional[str]:
        """
        Geçerli bir widget token'ından token'ın sahibi olan kullanıcının adını çıkarır.

        Args:
            token (str): Kullanıcı adının çıkarılacağı widget token'ı.

        Returns:
            Optional[str]: Token geçerliyse kullanıcı adı, değilse None.
        """
        # print(f"Token'dan kullanıcı adı alınıyor: {token[:20]}...") # Geliştirme için log
        is_valid, payload = self.validate_widget_token(token)
        if not is_valid or not payload:
            # print("Token geçersiz, kullanıcı adı alınamadı.") # Geliştirme için log
            return None
            
        username = payload.get('username')
        # if username:
            # print(f"Kullanıcı adı başarıyla alındı: {username}") # Geliştirme için log
        # else:
            # print("Token payload'unda kullanıcı adı bulunamadı.") # Geliştirme için log
        return username

# =============================================================================
# Widget Token Servis Modülü Sonu
# =============================================================================
