<?php
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


