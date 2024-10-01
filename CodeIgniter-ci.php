<?php
# Печатаме в конзолата на php
error_log('Some message ...');

# Зареждане на модел
// Зареждате модела, ако вече не е зареден
$this->load->model('Your_model');
$data = $this->Your_model->methodToGetSomeData();

# Заявка
// Подготовка на подзаявка за полагаемия отпуск
$this->db->select('user_id, SUM(days) as annual_leave, 0 as used_leave', false);
$this->db->from('annual_leave');
$this->db->group_by('user_id');
$subquery1 = $this->db->get_compiled_select();

// Подготовка на подзаявка за използвания отпуск
$this->db->select('user_id, 0 as annual_leave, SUM(days) as used_leave', false);
$this->db->from('leave');
$this->db->group_by('user_id');
$subquery2 = $this->db->get_compiled_select();

// Обединяване на подзаявките
$final_query = $this->db->query($subquery1 . ' UNION ALL ' . $subquery2);
// $this->db->last_query();  // debug

// Извличане на резултатите
$results = $final_query->result_array();

// Заявка пример
private function raw_sql() {
        $user_filter = $this->input->post('user_filter', true);
        $order_num_filter = $this->input->post('order_num_filter', true);
        // Начало на CI селект заявката
        $this->db->select('ord.id');
        $this->db->from('orders ord');
        // Добавяне на WHERE условията
        $this->db->group_start();
        $this->db->or_where('ord.status', 1);
        $this->db->or_where('ord.status', 2);
        $this->db->group_end();
        // AND
        $this->db->group_start();
        $this->db->or_where('ord.type', 1);
        $this->db->or_where('ord.type', 2);
        $this->db->group_end();
        // Добавяне на ORDER BY условията
        // $this->db->order_by('ord.priority', 'DESC');
        // $this->db->order_by('ord.order_num', 'ASC');
        // Добавяне на филтъра за order_num
        if(isset($order_num_filter) && $order_num_filter != '') {
            $this->db->where('ord.order_num', $order_num_filter);
        }
        if($user_filter != '') {
            $this->db->group_start();
            // Добавяне на филтъра за Потребител
            $this->db->join('users usr', 'usr.id = ord.user_id');
            $this->db->or_group_start();
            $this->db->like('usr.username', $user_filter);
            $this->db->or_like('usr.name', $user_filter);
            $this->db->or_like('usr.family', $user_filter);
            $this->db->or_like('usr.phone', $user_filter);
            $this->db->group_end();
            // OR
            // Добавяне на филтъра за Фирма
            $this->db->join('invoices inv', 'inv.id = ord.invoice_id');
            $this->db->or_group_start();
            $this->db->like('inv.firmname', $user_filter);
            $this->db->or_like('inv.firmBulstat', $user_filter);
            $this->db->group_end();
            // Добавяне на филтъра за Обект
            $this->db->join('av_addresses adr', 'adr.id = ord.address_id');
            $this->db->or_group_start();
            $this->db->like('adr.area', $user_filter);
            $this->db->or_like('adr.street', $user_filter);
            $this->db->group_end();
            $this->db->group_end();
        }
        // Ограничаване на резултатите
        $this->db->limit(9999);
        // Изпълнение на заявката
        $query = $this->db->get();
        $result = $query->result_array();
        $result = array_column($result, 'id');
        // Дебъг на заявката
        // echo $this->db->last_query(); exit();
        return $result ? $result : array(0);
    }

# Заявка
// Във вашия модел
public function get_leave_details() {
    $this->db->select('u.id, u.name, u.family, al.annual_leave, ts.used_leave');
    $this->db->from('users as u');
    $this->db->join('(SELECT user_id, SUM(days) as annual_leave FROM annual_leave GROUP BY user_id) as al', 'u.id = al.user_id', 'left');
    $this->db->join('(SELECT user_id, SUM(dayz) as   used_leave FROM        leave GROUP BY user_id) as l', 'u.id = l.user_id', 'left');
    $this->db->where('(COALESCE(al.annual_leave, 0) + COALESCE(ts.used_leave, 0)) > 0');
    $query = $this->db->get();

    return $query->result_array();
}

# Custom Log
<?php
function write_log($file_name, $log_type, $message) {
    // Форматиране на времето за лога
    $timestamp = date('Y-m-d H:i:s');
    // Форматиране на съобщението
    $formatted_message = "[{$timestamp}] {$log_type}: " . PHP_EOL . $message . PHP_EOL;
    // Записване на съобщението в лог файл
    file_put_contents($file_name, $formatted_message, FILE_APPEND);
}

try {
    // Вашият код, който може да хвърли изключение
} catch (Throwable $tr) {
    $this->CI =& get_instance();
    $input_data = $this->CI->input->post(); // общи входни данни ИЛИ подайте параметрите на виканата функция 
    write_log(
        'database_error.log', 
        'ERROR', 
        $this->CI->input->ip_address() . " function_name: " .
        $tr->__toString() . PHP_EOL . print_r($input_data, true)
    );
}
?>

catch (Throwable $tr) {
    write_log('database_error.log', 'ERROR', $this->CI->input->ip_address() . " function_name: " .
              $tr->__toString() . PHP_EOL . print_r($input_data, true));
}

# Рутиране
[application/config/routes.php]
// от метода на един контролер към друг метод на друг контролер
$route['product/delivery_product'] = 'info/delivery';

# composer
https://getcomposer.org/download/
php5.6 composer.phar update
# в папката на файла composer.jsonutoload.php
composer install  # създава папка vendor с файл autoload.php
require_once FCPATH . 'vendor/autoload.php';
require_once APPPATH . '../vendor/autoload.php';  # APPPATH съдържа пътя до директорията application

# включване на short_open_tag (<?) за стари сайтове
php --ini
phpinfo()
# за да разберем къде се намира файла php.ini и там променяме
short_open_tag = On

#cron job superhosting
/opt/cpanel/ea-php72/root/usr/bin/php /home/client-name/public_html/index.php controller_name method_name param_value
# ако не искаме email от cron job, анулираме изход от командата
 >/dev/null 2>&1
