url (to show woocommerce orders):
https://your-site.com/wp-admin/edit.php?post_type=shop_order

file:
/wp-content/plugins/woocommerce/includes/admin/list-tables/class-wc-admin-list-table-orders.php

function:
render_order_date_column()

append code:
$user  = get_user_by( 'id', $this->object->get_customer_id() );
echo $user->user_login;
global $wpdb;
$files = $wpdb->get_results("SELECT * FROM formcraft_3_files limit 1");
foreach( $files as $file ) {
    echo '<a href="' . $file->file_url . '" target="_blank">';
    echo '<img src="' . $file->file_url . '" width="50px" height="50px">';
    echo '</a>';
} 
