$(document).ready(function() {
    var form = $('#form_buying_product');

    function basketUpdating(item_id, item_price, nmb, is_delete) {
        var data = {};
        data.item_id = item_id;
        data.nmb = nmb;
        data.price = item_price;
        var csrf_token = $('#form_buying_product [name="csrfmiddlewaretoken"]').val();
        data["csrfmiddlewaretoken"] = csrf_token;

        if (is_delete){
            data["is_delete"] = true;
        }

        var url = form.attr("action");

         $.ajax({
             url: url,
             type: 'POST',
             data: data,
             cache: true,
             success: function (data) {
                 if (data.products_total_nmb || data.products_total_nmb == 0){
                    $('#basket_total_nmb').text("("+data.products_total_nmb+")");
                    $('.basket-items ul').html("");
                    $.each(data.items, function(k, v){
                        $('.basket-items ul').append('<li>'+ v.name+', ' + v.nmb + 'шт.' + v.price + '$  ' +
                            '<a class="delete-item" href="" data-item_id="'+v.id+'">x</a>'+
                            '</li>');
                     });
                 }

             },
             error: function(){
                 console.log("error")
             }
         })
    }

    form.on('submit', function(e){
        e.preventDefault();
        var nmb = $('#number').val();
        var submit_btn = $('#submit_btn');
        var item_id = submit_btn.data('item_id');
        var item_price = submit_btn.data('price');

        basketUpdating(item_id, item_price, nmb, is_delete=false);
    });

    function shovingBasket() {
        $('.basket-items').removeClass('hidden');
    }

    $('.basket_container').on('click, hover', function(e){
        e.preventDefault();
        shovingBasket();
    })

    $('.basket_container').mouseover(function(){
        shovingBasket();
    })

    $(document).on('click', '.delete-item', function(e){
        e.preventDefault();
        item_id = $(this).data('item_id');
        nmb = 0;
        item_price = 0;
        basketUpdating(item_id, item_price, nmb, is_delete=true);
    })
});