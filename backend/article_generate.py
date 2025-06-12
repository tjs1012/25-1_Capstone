from transformers.optimization import get_cosine_schedule_with_warmup
import torch
import pytorch_lightning as pl

class KoBARTConditionalGeneration(pl.LightningModule):
    def __init__(self, hparams, train_data_len=None, **kwargs):
        # super(KoBARTConditionalGeneration, self).__init__()
        super().__init__()
        self.hparams.update(hparams)
        self.train_data_len = train_data_len

        self.device_type = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # self.model = kwargs['model'].cuda()
        self.model = kwargs['model'].to(self.device_type)
        self.tokenizer = kwargs['tokenizer']

        self.model.train()

    def configure_optimizers(self):
        param_optimizer = list(self.model.named_parameters())
        no_decay = ['bias', 'LayerNorm.bias', 'LayerNorm.weight']

        optimizer_grouped_parameters = [{
            'params': [
                p for n, p in param_optimizer if not any(nd in n for nd in no_decay)
            ],
            'weight_decay': 0.01
        }, {
            'params': [
                p for n, p in param_optimizer if any(nd in n for nd in no_decay)
            ],
            'weight_decay': 0.0
        }]

        optimizer = torch.optim.AdamW(
            optimizer_grouped_parameters,
            lr = self.hparams.lr
        )

        # num_workers = gpus * num_nodes
        # data_len = len(self.train_dataloader().dataset)
        data_len = self.train_data_len

        num_train_steps = int(data_len / self.hparams.batch_size * self.hparams.max_epochs)

        num_warmup_steps = int(num_train_steps * self.hparams.warmup_ratio)

        scheduler = get_cosine_schedule_with_warmup(
            optimizer,
            num_warmup_steps=num_warmup_steps,
            num_training_steps=num_train_steps
        )

        lr_scheduler = {
            'scheduler': scheduler,
            'monitor': 'loss',
            'interval': 'step',
            'frequency': 1
        }

        return [ optimizer ], [ lr_scheduler ]

    def forward(self, inputs):
        return self.model(
            input_ids = inputs['input_ids'],
            attention_mask = inputs['attention_mask'],
            decoder_input_ids = inputs['decoder_input_ids'],
            decoder_attention_mask = inputs['decoder_attention_mask'],
            labels = inputs['labels'],
            return_dict = True
        )

    def training_step(self, batch, batch_idx):
        loss = self(batch).loss
        return loss

    def validation_step(self, batch, batch_idx):
        loss = self(batch).loss

    def test(self, text):
        tokens = self.tokenizer.encode("<s>" + text + "</s>")

        tokenLength = len(tokens)
        remain = self.hparams.max_length - tokenLength

        if remain >= 0:
            tokens = tokens + [ self.tokenizer.pad_token_id ] * remain
            attention_mask = [ 1 ] * tokenLength + [ 0 ] * remain
        else:
            tokens = tokens[: self.hparams.max_length - 1] + self.tokenizer.encode("</s>")
            attention_mask = [ 1 ] * self.hparams.max_length

        # tokens = torch.LongTensor([ tokens ]).cuda()
        # attention_mask = torch.LongTensor([ attention_mask ]).cuda()
        # self.model = self.model.cuda()
        tokens = torch.LongTensor([tokens]).to(self.device_type)
        attention_mask = torch.LongTensor([attention_mask]).to(self.device_type)
        self.model = self.model.to(self.device_type)

        result = self.model.generate( # generate: KoBART가 새로운 제목을 만들어내는 함수
            tokens,
            max_length = self.hparams.max_length,
            attention_mask = attention_mask,
            num_beams = 10 # 여러 후보를 고려하여 가장 좋은 결과를 선택하는 방식
        )[0]

        a = self.tokenizer.decode(result)
        return a
