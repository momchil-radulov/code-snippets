### product tabs ### 
wp-content/plugins/woocommerce/templates/single-product/tabs/tabs.php

# за да покажем атрибутите
добавяме след: if ( ! empty( $product_tabs ) ) : ?>
<?php
// Проверка дали таб с title "Specification" вече съществува
$tab_exists = false;
foreach ($product_tabs as $tab) {
    if (isset($tab['title']) && $tab['title'] === 'Specification') {
        $tab_exists = true;
        break;
    }
}
// Ако табът "Specification" не съществува, го добавяме
if (!$tab_exists) {
    $product_tabs['specification'] = [
        'title'    => 'Specification',
        'priority' => 15,
        'callback' => 'display_specification_content'
    ];
}
uasort($product_tabs, function ($a, $b) {
    return $a['priority'] <=> $b['priority']; // Сравнява приоритетите
});
function display_specification_content() {
    global $product;
    echo wc_display_product_attributes($product); // Показва атрибутите
}
?>


################################
url (for edit in wordpress)
https://you-site.com/wp-admin/plugin-editor.php?file=woocommerce%2Fincludes%2Fadmin%2Flist-tables%2Fclass-wc-admin-list-table-orders.php&plugin=woocommerce%2Fwoocommerce.php

url (to show woocommerce orders):
https://your-site.com/wp-admin/edit.php?post_type=shop_order

file:
/wp-content/plugins/woocommerce/includes/admin/list-tables/class-wc-admin-list-table-orders.php

function:
render_order_total_column()

append code:
echo '<br />';
//$user  = get_user_by( 'id', $this->object->get_customer_id() );
$telefon = get_user_meta($this->object->get_customer_id(), 'Telefon', true);
if ($telefon) {
	echo "Телефон " . $telefon;
}
$city = get_user_meta($this->object->get_customer_id(), 'City', true);
if ($city) {
	echo '<br />';
	echo "гр. " . $city;
}
$age = get_user_meta($this->object->get_customer_id(), 'Age', true);
if ($age) {
	echo '<br />';
	echo $age . " години";
}
/*global $wpdb;
$file = $wpdb->get_row("select *
                          from formcraft_3_submissions
                         where content like '%\\\"" . $user->user_login . "%'");
$content = json_decode(str_replace('\"', '"', $file->content), true);
foreach($content as $item) {
    if($item["label"] == "Telefon") {
        $phone = $item["value"];
	echo "Телефон " . $phone;
    }
}
*/

function:
render_order_date_column()

append code:
echo '<br />';
$user  = get_user_by( 'id', $this->object->get_customer_id() );
global $wpdb;
$file = $wpdb->get_row("select *
                          from formcraft_3_submissions
                         where content like '%\\\"" . $user->user_login . "%'");
$content = $file->content;
$content = str_replace('\"', '"', $content);
$content = str_replace("\'", "'", $content);
//echo $content;
$content = json_decode($content, true);
foreach($content as $item) {
    if($item["url"][0]) {
        $url = str_replace('\\/','/',$item["url"][0]);
        echo '<a href="' . $url . '" target="_blank">';
        echo '<img src="' . $url . '" width="50px" height: auto; ">';
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

url (for edit wp-admin/edit.php)
https://you-site.com:2083/cpsess7330492454/frontend/paper_lantern/filemanager/editit.html?file=edit.php&fileop=&dir=%2Fhome%2Fistinski%2Fautomateyour.store%2Fwp-admin&dirop=&charset=&file_charset=_DETECT_&baseurl=&basedir=&edit=1
add code:
/*
echo '123123123';
$included_files = get_included_files();
$counter = 0;
foreach ($included_files as $filename) {
    $counter++;
    echo "$filename\n";
}
echo $counter;
*/

url (for edit wp-admin/post.php)
https://you-site.com:2083/cpsess7330492454/frontend/paper_lantern/filemanager/editit.html?file=post.php&fileop=&dir=%2Fhome%2Fistinski%2Fautomateyour.store%2Fwp-admin&dirop=&charset=&file_charset=_DETECT_&baseurl=&basedir=&edit=1
