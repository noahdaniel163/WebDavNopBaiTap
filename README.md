# Teacher WebDAV Manager

Phần mềm hỗ trợ giáo viên thu bài tập của học sinh qua mạng LAN một cách đơn giản, nhanh chóng, không cần Internet.

## 🚀 Tính năng chính

*   **Dành cho Học sinh**:
    *   Giao diện web đơn giản để nộp bài tập.
    *   Chỉ được phép Upload, không được xem hoặc xóa bài của người khác.
    *   Tự động đổi tên file nếu trùng (ví dụ: `bai_tap.docx` -> `bai_tap_01.docx`) để tránh ghi đè bài của bạn khác.
*   **Dành cho Giáo viên**:
    *   Giao diện quản lý (GUI) trên Windows dễ sử dụng.
    *   Tùy chỉnh thư mục lưu bài tập (ổ D, USB...).
    *   Đăng nhập Admin để xem danh sách file, tải về hoặc xóa file rác.
    *   Hỗ trợ lớp học đông người (60+ học sinh) nhờ Web Server tối ưu (Waitress).

## 🛠️ Hướng dẫn cài đặt & Build file EXE

Nếu bạn muốn tự đóng gói phần mềm thành file `.exe` để chạy trên máy khác:

1.  **Cài đặt Python**: Tải và cài đặt Python 3.10 trở lên.
2.  **Cài đặt thư viện**:
    Mở CMD/Terminal tại thư mục dự án và chạy:
    ```bash
    pip install -r requirements.txt
    pip install pyinstaller waitress requests
    ```
3.  **Đóng gói (Build)**:
    Chạy file `build_exe.bat` hoặc dùng lệnh:
    ```bash
    pyinstaller --noconfirm --onefile --windowed --add-data "templates;templates" --name "WebDAV_Manager_GUI" gui_launcher.py
    ```
4.  **Kết quả**:
    File `WebDAV_Manager_GUI.exe` sẽ nằm trong thư mục `dist`. Bạn chỉ cần copy file này đi là dùng được.

## 📖 Hướng dẫn sử dụng

1.  **Chạy phần mềm**: Mở `WebDAV_Manager_GUI.exe`.
2.  **Cấu hình**:
    *   **Host IP**: Để mặc định `0.0.0.0` để các máy trong LAN có thể truy cập.
    *   **Port**: Mặc định `8080` (có thể đổi nếu bị trùng).
    *   **Admin User/Pass**: Đặt tài khoản để giáo viên quản trị (Mặc định: `admin` / `123456`).
    *   **Folder chứa bài**: Chọn thư mục trên máy (hoặc USB) để lưu bài nộp.
3.  **Bắt đầu**: Bấm nút **"Start Server"**.
4.  **Cho học sinh nộp bài**:
    *   Cung cấp địa chỉ IP của máy giáo viên cho học sinh (Ví dụ: `http://192.168.1.50:8080`).
    *   Học sinh truy cập vào web và chọn file để nộp.
5.  **Quản lý bài**:
    *   Giáo viên bấm nút "Mở Web" trên phần mềm.
    *   Bấm vào **"Giáo viên đăng nhập"** và điền tài khoản để quản lý file.

## 🛑 Dừng chương trình
*   Bấm nút **"Stop Server"** để ngắt kết nối.
*   Bấm **"Exit"** để thoát hoàn toàn.

## 📂 Cấu trúc thư mục
*   `gui_launcher.py`: File chạy chính (Giao diện).
*   `app.py`: Server xử lý logic (Flask).
*   `templates/`: Thư mục chứa giao diện Web (HTML).
*   `config.json`: File lưu cấu hình (tự sinh ra khi chạy).
