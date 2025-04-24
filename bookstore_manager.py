import os  # 為了清理頁面而導入的模組
import sqlite3

DB_NAME = "bookstore.db"  # 你可以視情況修改檔名


def connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME)  # 連線資料庫
    conn.row_factory = sqlite3.Row  # 設置row_factory
    return conn


def initialize_db(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()  # 建立 cursor 物件
    try:
        # 建立範例資料表
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS member (
            mid TEXT PRIMARY KEY,
            mname TEXT NOT NULL,
            mphone TEXT NOT NULL,
            memail TEXT
        );

        CREATE TABLE IF NOT EXISTS book (
            bid TEXT PRIMARY KEY,
            btitle TEXT NOT NULL,
            bprice INTEGER NOT NULL,
            bstock INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sale (
            sid INTEGER PRIMARY KEY AUTOINCREMENT,
            sdate TEXT NOT NULL,
            mid TEXT NOT NULL,
            bid TEXT NOT NULL,
            sqty INTEGER NOT NULL,
            sdiscount INTEGER NOT NULL,
            stotal INTEGER NOT NULL
        );

        INSERT OR IGNORE INTO member VALUES
            ('M001', 'Alice', '0912-345678', 'alice@example.com'),
            ('M002', 'Bob', '0923-456789', 'bob@example.com'),
            ('M003', 'Cathy', '0934-567890', 'cathy@example.com');

        INSERT OR IGNORE INTO book VALUES
            ('B001', 'Python Programming', 600, 50),
            ('B002', 'Data Science Basics', 800, 30),
            ('B003', 'Machine Learning Guide', 1200, 20);

        INSERT OR IGNORE INTO sale (sid, sdate, mid, bid, sqty, sdiscount,
                                    stotal) VALUES
            (1, '2024-01-15', 'M001', 'B001', 2, 100, 1100),
            (2, '2024-01-16', 'M002', 'B002', 1, 50, 750),
            (3, '2024-01-17', 'M001', 'B003', 3, 200, 3400),
            (4, '2024-01-18', 'M003', 'B001', 1, 0, 600);
        """)
        conn.commit()
    except sqlite3.Error as e:
        print(f"=> 初始化資料表失敗：{e}")
        conn.rollback()


def add_sale(conn: sqlite3.Connection, sdate: str, mid: str, bid: str,
             sqty: int, sdiscount: int) -> tuple[bool, str]:
    cursor = conn.cursor()

    # 驗證會員是否存在
    cursor.execute("SELECT mid FROM member WHERE mid = ?", (mid, ))
    if cursor.fetchone() is None:
        return False, "錯誤：會員編號或書籍編號無效"

    # 驗證書籍是否存在
    cursor.execute("SELECT bid FROM book WHERE bid = ?", (bid, ))
    if cursor.fetchone() is None:
        return False, "錯誤：會員編號或書籍編號無效"

    # 新增資料
    cursor.execute("SELECT bprice FROM book WHERE bid = ?", (bid, ))
    bprice = cursor.fetchone()[0]
    stotal = bprice * sqty - sdiscount  # 算價格
    try:
        cursor.execute("""INSERT INTO sale (sdate, mid, bid, sqty, sdiscount,
                       stotal) VALUES (?,?,?,?,?,?)""",
                       (sdate, mid, bid, sqty, sdiscount, stotal))
        conn.commit()

    except sqlite3.Error:
        conn.rollback()

    # 檢查庫存
    cursor.execute("SELECT bstock FROM book WHERE bid = ?", (bid, ))
    bstock = cursor.fetchone()[0]

    # 若庫存不足，則傳回訊息；若庫存足夠，則將庫存更新
    if sqty > bstock:
        return False, f"錯誤：書籍庫存不足 (現有庫存: {bstock})"
    else:
        cursor.execute("UPDATE book SET bstock = bstock - ? WHERE bid = ?",
                       (sqty, bid))
        conn.commit()

    # 避免出現sqlite3.OperationalError: database is locked
    conn.close()

    # 若上面檢查皆OK，那就傳回已新增的訊息
    return True, f"銷售記錄已新增！(銷售總額: {stotal})"


def print_sale_report(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    # 使用inner join找出我們需要印出的資料
    cursor.execute("""SELECT sid, sdate, mname, btitle,
                bprice, sqty, sdiscount, stotal
                FROM sale AS s
                INNER JOIN member AS m ON s.mid = m.mid
                INNER JOIN book AS b ON s.bid = b.bid
                ORDER BY sid ASC""")
    rows = cursor.fetchall()

    if not rows:
        print("=> 目前沒有銷售資料")
        return

    n = 1
    print("\n==================== 銷售報表 ====================")

    for row in rows:
        print(f"銷售 #{n}")
        print(f"銷售編號: {row['sid']}")
        print(f"銷售日期: {row['sdate']}")
        print(f"會員姓名: {row['mname']}")
        print(f"書籍標題: {row['btitle']}")
        print("--------------------------------------------------")
        print("{:<4}\t{:<4}\t{:<4}\t{:<6}"
              .format("單價", "數量", "折扣", "小計"))
        print("--------------------------------------------------")

        print("{:<6,}\t{:<6}\t{:<6,}\t{:<6,}"
              .format(row["bprice"], row["sqty"],
                      row["sdiscount"], row["stotal"]))

        print("--------------------------------------------------")
        print(f"銷售總額: {row['stotal']:,}")
        print("==================================================\n")
        n += 1


def update_sale(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    print("\n======== 銷售記錄列表 ========")
    cursor.execute("""SELECT sid, mname, sdate FROM sale AS s
                   INNER JOIN member AS m ON s.mid = m.mid
                   ORDER BY sid ASC""")
    rows = cursor.fetchall()

    if not rows:
        print("=> 目前沒有銷售資料")
        return
    n = 1

    for row in rows:
        print("{0}. 銷售編號: {1} - 會員: {2} - 日期: {3}"
              .format(n, row["sid"], row["mname"], row["sdate"]))
        n += 1
    print("================================")

    # 檢查輸入的sid在銷售編號的資料中是否存在
    while True:
        sid = input("請選擇要更新的銷售編號 (輸入數字或按 Enter 取消): ")
        cursor.execute("SELECT sid FROM sale WHERE sid = ?", (sid, ))

        # Enter 鍵退出，回首頁
        if sid == "":
            os.system("clear")
            main()
            break

        # 若不存在就輸出查無此筆資料
        if cursor.fetchone() is None:
            print("=> 錯誤：銷售編號無效，請再輸入一次")
            continue
        break

    # 輸入新的折扣金額
    while sid != "":
        try:
            new_sdiscount = int(input("請輸入新的折扣金額："))
            if new_sdiscount < 0:
                print("=> 錯誤：折扣金額不能為負數，請重新輸入")
                continue
            break
        except ValueError:
            print("=> 錯誤：數量或折扣必須為整數，請重新輸入")
            continue

    # 計算新的折扣後的銷售總額
    cursor.execute("SELECT sdiscount, stotal FROM sale WHERE sid = ?", (sid, ))
    old_sdiscount, stotal = cursor.fetchone()
    stotal += (old_sdiscount - new_sdiscount)

    # 將新折扣與新總額填入資料表修改
    cursor.execute("UPDATE sale SET sdiscount = ?, stotal = ? WHERE sid = ?",
                   (new_sdiscount, stotal, sid))
    conn.commit()
    conn.close()
    print(f"=> 銷售編號 {sid} 已更新！(銷售總額: {stotal})")


def main():
    conn = connect_db()
    initialize_db(conn)
    print("***************選單***************")
    print("1. 新增銷售記錄")
    print("2. 顯示銷售報表")
    print("3. 更新銷售記錄")
    print("4. 刪除銷售記錄")
    print("5. 離開")
    print("**********************************")
    choice = input("請選擇操作項目(Enter 離開)：")

    if choice == "1":
        sdate = input("請輸入銷售日期 (YYYY-MM-DD)：")
        mid = input("請輸入會員編號：")
        bid = input("請輸入書籍編號：")

        # 檢查數量
        while True:
            try:
                sqty = int(input("請輸入購買數量："))
                if sqty <= 0:
                    print("=> 錯誤：數量必須為正整數，請重新輸入")
                    continue
                break
            except ValueError:
                print("=> 錯誤：數量或折扣必須為整數，請重新輸入")
                continue

        # 檢查折扣
        while True:
            try:
                sdiscount = int(input("請輸入折扣金額："))
                if sdiscount < 0:
                    print("=> 錯誤：折扣金額不能為負數，請重新輸入")
                    continue
                break
            except ValueError:
                print("=> 錯誤：數量或折扣必須為整數，請重新輸入")
                continue

        yesno, msg = add_sale(connect_db(), sdate, mid, bid, sqty, sdiscount)
        print("=>", msg)

    elif choice == "2":
        print_sale_report(connect_db())

    elif choice == "3":
        update_sale(connect_db())

    elif choice == "4":
        print("4")
    # choice == "" >>> 直接Enter離開
    elif choice == "5" or choice == "":
        exit()
    else:
        print("=> 請輸入有效的選項（1-5）")
        main()

    conn.close()


if __name__ == "__main__":
    main()
