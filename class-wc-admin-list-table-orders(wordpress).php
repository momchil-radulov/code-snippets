url (for edit in wordpress)
https://you-site.com/wp-admin/plugin-editor.php?file=woocommerce%2Fincludes%2Fadmin%2Flist-tables%2Fclass-wc-admin-list-table-orders.php&plugin=woocommerce%2Fwoocommerce.php

url (to show woocommerce orders):
https://your-site.com/wp-admin/edit.php?post_type=shop_order

file:
/wp-content/plugins/woocommerce/includes/admin/list-tables/class-wc-admin-list-table-orders.php

function:
render_order_date_column()

append code:
$user  = get_user_by( 'id', $this->object->get_customer_id() );
global $wpdb;
$file = $wpdb->get_row("select *
                          from formcraft_3_submissions
                         where content like '%\\\"" . $user->user_login . "%'");
$content = json_decode(str_replace('\"', '"', $file->content), true);
foreach($content as $item) {
    if($item["url"][0]) {
        $url = str_replace('\\/','/',$item["url"][0]);
        echo '<a href="' . $url . '" target="_blank">';
        echo '<img src="' . $url . '" width="50px" height="50px">';
        echo '</a>';
    }
}
/*
echo $user->user_login;
$files = $wpdb->get_results("SELECT * FROM formcraft_3_files where id =
    (select id from formcraft_3_submissions where content like '%\\\"" . $user->user_login . "%')");
foreach( $files as $file ) {
    echo '<a href="' . $file->file_url . '" target="_blank">';
    echo '<img src="' . $file->file_url . '" width="50px" height="50px">';
    echo '</a>';
}
*/
