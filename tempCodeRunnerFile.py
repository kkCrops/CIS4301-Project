def test_edit_user(self):
        new_user = self.get_user()
        new_user.account_id = "test_id"
        original_account_id = "0cf25a005473"

        self.db.edit_user(original_account_id=original_account_id, new_user=new_user)

        self.db.cur.execute("SELECT account_id, name, address, phone_number, email "
                         "FROM User WHERE account_id = %s", (new_user.account_id,))

        edited_user = self.db.cur.fetchone()

        self.db.cur.execute("SELECT account_id, name, address, phone_number, email "
                         "FROM User WHERE account_id = %s", (original_account_id,))

        old_user = self.db.cur.fetchone()

        self.assertIsNone(old_user)

        self.assertEqual(new_user.account_id, edited_user[0])
        self.assertEqual(new_user.name, edited_user[1])
        self.assertEqual(new_user.address, edited_user[2])
        self.assertEqual(new_user.phone_number, edited_user[3])
        self.assertEqual(new_user.email, edited_user[4])
