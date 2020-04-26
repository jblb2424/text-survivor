
$(document).ready(() => {
  document.querySelector('#play').onclick = function(e) {
    $.ajax({
        url: 'http://127.0.0.1:8000/home/load_room/',
        type: "GET",
        dataType: "json",
        success: function (data) {
        window.location.pathname = '/home/' + data.room_id + '/';
        }
    });
  }
});