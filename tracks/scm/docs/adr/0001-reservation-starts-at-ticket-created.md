# Reservasi stok dimulai saat `ticket.created`, bukan saat order

Brief SCM menahan stok 72 jam sejak CRM mencatat order. Di arsitektur ini SCM tidak pernah melihat order: CRM hanya mengirim `ticket.created` setelah pembayaran, jadi Reservasi lahir dari `StockRequest` yang READY_TO_ISSUE dan kedaluwarsa 72 jam kemudian. Reservasi tidak parsial (kurang satu baris berarti `PENDING_STOCK` tanpa tahanan), dan pelepasan hanya lewat kedaluwarsa atau pembatalan manual karena belum ada event pembatalan tiket di kontrak.

Alternatif yang ditolak: meminta CRM mengirim event order ke SCM (kontrak baru, menahan stok untuk order yang belum bayar, mengulang masalah P-02).
