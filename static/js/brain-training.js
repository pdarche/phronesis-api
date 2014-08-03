$(document).ready(function(){
  // var template
  // $.get('/static/js/templates/papers.handlebars', function(data){
  //   template = data
  // })
  $.getJSON('/api/brain',function(data){
    $('#create .game').autocomplete({
      source: _.map(data['data'],function(d){
        return {"label": d['name'], "value": d['id']}
      })
    })
  })

  $('#brain_nav li').on('click', function(ev){
    var $this = $(ev.target)
      , active = $('.active')
      , attr = $this.attr('id')

    active.removeClass('active')
    $this.addClass('active')

    $('#controls').children().hide()
    $('.'+attr).show()
  })


  $("#create input[type='submit']").on('click', function(ev){
    ev.preventDefault()
    var el = $('#create')
      , game_id = el.find('.game').val()
      , score = el.find('.score').val()
      , data;

    data = {
      'game_id' : game_id,
      'score'   : score,
    }

    $.ajax({
      url: '/api/brain',
      type: 'POST',
      data: data,
      success: function(){
        alert('success')
      },
      error: function(){
        alert('error')
      }
    })  
  })

  // $('.edit').on('click', function(){

  // })

  // $('body').on('click', '.abstract h5, #controls h3', function(ev){
  //   var target = $(ev.target)

  //   if (!(target.next().hasClass('hidden'))){
  //     target.next().addClass('hidden')
  //   } else {
  //     target.next().removeClass('hidden')
  //   }
  // })
})

// function renderTemplates(template, papers){
//   var source   = $(template).html();
//   var tmpl     = Handlebars.compile(source);
//   var html     = tmpl({"papers":papers})

//   $('#papers').html(html)
// }
