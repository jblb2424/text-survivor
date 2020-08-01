$(document).ready(() => {
  localStorage.removeItem('state')
  document.querySelector('#play').onclick = function(e) {
    $.ajax({
        url: domain + 'load_room/',
        type: "GET",
        dataType: "json",
        success: function (data) {
        window.location.pathname = '/' + data.room_id + '/';
        }
    })};
  document.querySelector('#create-game-public').onclick = function(e) {
    $.ajax({
        url: domain + 'create_public_room/',
        type: "GET",
        dataType: "json",
        success: function (data) {
        window.location.pathname = '/' + data.room_id + '/';
        }
    })};
  document.querySelector('#create-game-private').onclick = function(e) {
    $.ajax({
        url: domain + 'create_private_room/',
        type: "GET",
        dataType: "json",
        success: function (data) {
        window.location.pathname = '/' + data.room_id + '/';
        }
    })};
});