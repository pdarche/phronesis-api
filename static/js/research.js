$(document).ready(function(){
  var template
  $.get('/static/js/templates/papers.handlebars', function(data){
    template = data
  })

  $('#research_nav').on('click', 'li', function(ev){
    var $this = $(ev.target)
      , active = $('.active')
      , targetAttr = $this.attr('class').split(' ')[0]
      , currAttr = active.attr('class').split(' ')[0]
    
    $('#' + currAttr).hide()
    $('#' + targetAttr).show()

    active.removeClass('border')
          .removeClass('active')

    $this.addClass('active')
         .addClass('border')
    
  })

  $('#search input').keyup(function(){
    var el = $(this)
      , param = el.attr('name') 
      , value = el.val()
      , isFavorite = el.parent().find('.favorite').is(":checked")
      , data;

    data = {
      'param_name': param,
      'value': value,
      'favorite': isFavorite
    }

    $.getJSON('/api/research', data, function(data){
      renderTemplates(template, data['data'])
    })
  })

  $("#create input[type='submit']").on('click', function(ev){
    ev.preventDefault()
    var el = $('#create')
      , title = el.find('.title').val()
      , url = el.find('.url').val()
      , keywords = el.find('.keywords').val()
      , adjectives = el.find('.adjectives').val()
      , note = el.find('.note').val()
      , abstract = el.find('.abstract').val()
      , favorite = el.find('.favorite').is(":checked")
      , data;

    data = {
      'title'     : title,
      'url'       : url,
      'keywords'  : keywords,
      'adjectives': adjectives,
      'note'      : note,
      'abstract'  : abstract,
      'favorite'  : favorite
    }

    $.ajax({
      url: '/api/research',
      type: 'POST',
      data: data,
      success: function(){
        alert('success')
        el.find('input, textarea').val('')
      },
      error: function(){
        alert('error')
      }
    })  
  })

  $('.edit').on('click', function(){

  })

  $('body').on('click', '.abstract h5, #controls h3', function(ev){
    var target = $(ev.target)

    if (!(target.next().hasClass('hidden'))){
      target.next().addClass('hidden')
    } else {
      target.next().removeClass('hidden')
    }
  })
})

function renderTemplates(template, papers){
  var source   = $(template).html()
    , tmpl     = Handlebars.compile(source)
    , html     = tmpl({"papers":papers});

  $('#papers').html(html)
}
