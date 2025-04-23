import sqlite3

conn = sqlite3.connect('bookstore.db')  # 連線資料庫
conn.row_factory = sqlite3.Row # 設置row_factory
cursor = conn.cursor()  # 建立 cursor 物件


def add_sale(conn: sqlite3.Connection, sdate: str, mid: str, bid: str,
             sqty: int, sdiscount: int) -> tuple[bool, str]:

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
    stotal = bprice * sqty - sdiscount # 算價格
    try:
        cursor.execute("""INSERT INTO sale (sdate, mid, bid, sqty, sdiscount,
                    stotal) VALUES (?,?,?,?,?,?)""",
                    (sdate, mid, bid, sqty, sdiscount, stotal))
        conn.commit()
        cursor.execute("UPDATE book SET bstock = bstock - ? WHERE bid = ?",
                       (sqty, bid))
        conn.commit()
        # 避免出現 sqlite3.OperationalError: database is locked
        conn.close()
    except sqlite3.Error:
        conn.rollback()

    return False, f"銷售記錄已新增！(銷售總額: {stotal})"


def main():
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
                # 檢查庫存
                cursor.execute("SELECT bstock FROM book WHERE bid = ?", (bid, ))
                bstock = cursor.fetchone()[0]
                if sqty <= 0:
                    print("=> 錯誤：數量必須為正整數，請重新輸入")
                    continue
                elif sqty > bstock:
                    print(f"=> 錯誤：書籍庫存不足 (現有庫存: {bstock})")
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

        yesno, msg = add_sale(conn, sdate, mid, bid, sqty, sdiscount)
        print("=>", msg)

    elif choice == "2":
        print("2")
    elif choice == "3":
        print("3")
    elif choice == "4":
        print("4")
    # choice == "" >>> 直接Enter離開
    elif choice == "5" or choice == "":
        exit()
    else:
        print("=> 請輸入有效的選項（1-5）")
        main()
main()
