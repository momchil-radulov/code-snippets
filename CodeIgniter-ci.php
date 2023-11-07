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
