# Credit Card Designs Library

This is a large collection of credit/debit card backgrounds.

Why? Because it's fun! You can lust after the beautiful design of that card
you've always wanted. Or admire the fact that one issuer put Pikachu on a
credit card.

## Contributing

Contributions of new card images or physical scans are welcome!


Open a [pull request](https://github.com/ab/card-designs/pulls) on GitHub or email us at card-designs@googlegroups.com.

### Extracting card images from Apple Wallet

If you have a Mac with touch ID, you can extract high res card images from
Apple Pay Wallet.

Run this script in terminal:

```sh
mkdir ~/Desktop/cards
files=(~/Library/Passes/Cards/*.pkpass/cardBackgroundCombined@2x.png)
i=0
for f in "${files[@]}"; do
    i=$(( i + 1 ))
    cp $f ~/Desktop/cards/$i.png
done
```

### Downloading card images from PayPal

- On the web, visit [PayPal > Wallet](https://www.paypal.com/myaccount/money/)
- Click on the desired card to open the card detail page
- Right click on the card image
- Save image as...

The original title should be `image__140.png`. Rename it to something more meaningful.

You can also open the image in a new tab to confirm it's the expected card background.

## Other Collections

Collection by the author of Churner's Digest:
https://fearthez.com/2022/01/23/card-designs/

Collection by [u/chaoxu](https://www.reddit.com/user/chaoxu/):
https://dynalist.io/d/ldKY6rbMR3LPnWz4fTvf_HCh

## License

The card images remain copyrighted by the issuers, but we believe that it is
fair use to reproduce them here for non-commercial reference purposes. See
[LICENSE-CARDS.md](./LICENSE-CARDS.md)

All other material in this repository is released under the
[Mozilla Public License](./LICENSE).
