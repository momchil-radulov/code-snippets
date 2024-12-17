<?php
# Използвай FCPATH за файлове и директории, а base_url() за URL адреси.
# Печатаме в конзолата на php
error_log('Some message ...');

# Зареждане на модел
// Зареждате модела, ако вече не е зареден
$this->load->model('Your_model');
$data = $this->Your_model->methodToGetSomeData();

# Заявка
$this->db->select('p.id as product_id', false);
$this->db->from('products p');

$this->db->where('p.id =', $id); or direct ('p.id = 1')

$this->db->group_start(); // Започваме групиране на условията
$this->db->where('p.color !=', $color);
$this->db->or_where('p.color !=', $color_2);
$this->db->where_in('p.color', [$color, $color_2]);
$this->db->group_end(); // Завършваме групиране

$this->db->order_by('p.product_name', 'ASC');
$this->db->order_by('p.product_name', 'DESC');

$query = $this->db->get();
if ($query->num_rows() === 0) {
    // empty result
}
Връща един ред като асоциативен масив.
$result = $query->row_array();
Връща всички редове като асоциативен масив.
$result = $query->result_array();

Връща един ред като обект.
$result = $query->row()
Връща всички редове като обект.
$result = $query->result()
Връща една стойност от колонка от един ред 
$result = $query->row()->column_name

Обхождане и модифициране на резултата
$order_comments = $query->result_array();
foreach ($order_comments as &$comment) {
    $user_obj = $this->User_manager->getObj($comment['user_id']);
    $comment['user'] = $user_obj->getName();
}
// След цикъла трябва да премахнеш референцията
unset($comment);
// добавяне в началото на масива
array_unshift($order_comments, ['user_id' => 0, 'user' => 'Анонимен потребител']);

# UPDATE
public function setDeleted($id) {
        $this->db->where('id', $id);
        $result = $this->db->update('table_name', ['deleted' => 1]);
        return $result;
}

# INSERT
$data = array(
    'column1' => 'value1',
    'column2' => 'value2',
    'user_id' => $this->session->userdata('user_id');
);
if (   $this->db->insert('table_name', $data)   ) {
    echo "Записът е добавен успешно!";
} else {
    echo "Грешка при добавяне на записа.";
}
# debug generated sql
$this->db->set($data);
$sql = $this->db->get_compiled_insert('table_name');
echo $sql;

### transactions
## auto transaction
$this->db->trans_start();
...
ако възникне грешка някъде при db, се извършва auto rollback
# Завършваме транзакцията
$this->db->trans_complete();
//Проверяваме дали транзакцията е успешна
if ($this->db->trans_status() === FALSE) {
    // Ако не е успешна, връщаме грешка или изпълняваме алтернативни действия
    return false;
}
return true;
## manual transaction
$this->db->trans_begin();
# ако се наложи завършваме така
$this->db->trans_rollback();
# ИЛИ завършваме транзакцията така
if ($this->db->trans_status() === FALSE) {
    $this->db->trans_rollback();
}
else {
    $this->db->trans_commit();
}


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

<?php
# Object oriented programming
class Some_class extends Onother_class
{
    function __construct() {
        parent::__construct();
    }

    public function page() {
        // parent::page();
        or some code that overload the parent
    }
}

    
catch (Throwable $tr) {
    write_log('database_error.log', 'ERROR', $this->CI->input->ip_address() . " function_name: " .
              $tr->__toString() . PHP_EOL . print_r($input_data, true));
}

########################
### qrcode generator ###
########################

defined('BASEPATH') OR exit('No direct script access allowed');

class QrcodeController extends CI_Controller {

    public function index() {
        $this->load->library('Ciqrcode'); // Зареждане на библиотеката

        // Параметри за генериране на QR кода
        $params['data'] = base_url('upload'); // Линк към страницата за качване
        $params['size'] = 10; // Размер на QR кода
        $params['level'] = 'H'; // Ниво на корекция на грешките (L, M, Q, H)

        // ИЗХОДЕН буфер, за да уловим директния изход
        ob_start();
        $this->ciqrcode->generate($params);
        $qrCodeString = ob_get_clean(); // Съхраняваме изхода като string
        // Конвертиране на резултата в Base64 за изобразяване
        $base64QRCode = 'data:image/png;base64,' . base64_encode($qrCodeString);
        // Зареждане на изгледа с вграден QR код
        $this->data['qrCode'] = $base64QRCode;
        // ИЛИ записваме във файл
        $params['savename'] = QRCODES_FILE_PATH . $card_id . '.png';
        $this->ciqrcode->generate($params);
        $this->data['qrCode'] = QRCODES_FILE_PATH . $card_id . '.png';

        $this->load->view('qrcode_view', $this->data);
    }
}

във view: <img src="<?= $qrCode ?>" alt="QR Code">


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
